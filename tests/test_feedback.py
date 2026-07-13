import csv

import pytest

import services.feedback as fb
from services.feedback import save_feedback
from vision.feature_extractor import FaceFeatures

FEATURES = FaceFeatures(face_shape="Round", hair_type="Curly", hair_texture="Thick", gender="Male")


def _read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


@pytest.fixture(autouse=True)
def force_csv(monkeypatch):
    """Always use CSV fallback in tests — prevents accidental Firestore writes."""
    monkeypatch.setattr(fb, "_firestore_client", lambda: None)


class _FakeDB:
    def __init__(self):
        self.docs = []

    def collection(self, name):
        assert name == fb.FIRESTORE_COLLECTION  # Case 3: validates collection name
        return self

    def add(self, record):
        self.docs.append(record)


class _BrokenDB(_FakeDB):
    def add(self, record):
        raise RuntimeError("Firestore unavailable")


# ── CSV fallback tests ────────────────────────────────────────────────────────

def test_save_feedback_creates_file_with_header(tmp_path):
    path = str(tmp_path / "feedback.csv")
    save_feedback(satisfied=True, features=FEATURES, input_sources=["image", "text"], path=path)

    rows = _read_rows(path)
    assert len(rows) == 2
    assert rows[0][:2] == ["timestamp_utc", "satisfied"]
    assert rows[0][-1] == "suggestion"
    assert rows[1][1] == "yes"
    assert rows[1][2] == "image+text"
    assert rows[1][3:7] == ["Round", "Curly", "Thick", "Male"]
    assert rows[1][7] == ""


def test_save_feedback_appends_without_duplicate_header(tmp_path):
    path = str(tmp_path / "feedback.csv")
    save_feedback(satisfied=True, features=FEATURES, input_sources=["image"], path=path)
    save_feedback(satisfied=False, features=FEATURES, input_sources=["text"], path=path)

    rows = _read_rows(path)
    assert len(rows) == 3
    assert rows[2][1] == "no"
    assert rows[2][2] == "text"


def test_save_feedback_records_suggestion(tmp_path):
    path = str(tmp_path / "feedback.csv")
    save_feedback(
        satisfied=False,
        features=FEATURES,
        input_sources=["image"],
        suggestion="  I would prefer a buzz cut instead.  ",
        path=path,
    )

    rows = _read_rows(path)
    assert rows[1][1] == "no"
    assert rows[1][7] == "I would prefer a buzz cut instead."


# ── Firestore path tests ──────────────────────────────────────────────────────

def test_save_feedback_uses_firestore_when_available(monkeypatch):
    fake_db = _FakeDB()
    monkeypatch.setattr(fb, "_firestore_client", lambda: fake_db)

    save_feedback(satisfied=True, features=FEATURES, input_sources=["image", "text"])

    assert len(fake_db.docs) == 1
    doc = fake_db.docs[0]
    assert doc["satisfied"] == "yes"
    assert doc["input_sources"] == "image+text"
    assert doc["face_shape"] == "Round"
    assert doc["gender"] == "Male"
    assert doc["suggestion"] == ""


def test_firestore_failure_falls_back_to_csv(monkeypatch, tmp_path):
    """Case 1: Firestore write error → CSV fallback, no data loss."""
    monkeypatch.setattr(fb, "_firestore_client", lambda: _BrokenDB())

    path = str(tmp_path / "feedback.csv")
    save_feedback(satisfied=True, features=FEATURES, input_sources=["text"], path=path)

    rows = _read_rows(path)
    assert len(rows) == 2
    assert rows[1][1] == "yes"


def test_suggestion_truncated_to_max_length(monkeypatch, tmp_path):
    """Case 4: server-side cap — UI max_chars is client-side only."""
    path = str(tmp_path / "feedback.csv")
    long_suggestion = "x" * 1000
    save_feedback(
        satisfied=False,
        features=FEATURES,
        input_sources=["text"],
        suggestion=long_suggestion,
        path=path,
    )

    rows = _read_rows(path)
    assert len(rows[1][7]) == fb._SUGGESTION_MAX
