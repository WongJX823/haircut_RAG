import csv

from services.feedback import save_feedback
from vision.feature_extractor import FaceFeatures

FEATURES = FaceFeatures(face_shape="Round", hair_type="Curly", hair_texture="Thick", gender="Male")


def _read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


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
