"""
Happy-path (and key unhappy-path) tests for the full pipeline.

Everything that costs money or needs the network is mocked at the pipeline
boundary: feature extraction, same-person check, and the RAG recommendation.
What's really being tested is the orchestration in services/pipeline.py —
validation order, multi-input merging, gender consistency, and the result
contract the UI depends on. This is the regression suite: run it after
every change with `python -m pytest`.
"""

import json

import pytest

import services.pipeline as pipeline
from services.pipeline import run_pipeline
from services.validator import ValidationResult
from vision.feature_extractor import FaceFeatures
from rag.recommender import StructuredRecommendation, HaircutOption


def _recommendation():
    return {
        "recommendation": StructuredRecommendation(
            summary="Here are your best options.",
            haircuts=[
                HaircutOption(
                    name="Undercut",
                    why_it_works="Short sides slim a round face.",
                    styling_tip="Curl cream.",
                    maintenance="Every 4 weeks.",
                ),
                HaircutOption(
                    name="French Crop",
                    why_it_works="Fringe adds structure.",
                    styling_tip="Matte clay.",
                    maintenance="Every 3-4 weeks.",
                ),
            ],
            style_to_avoid="Bowl Cut",
            avoid_reason="Adds width.",
        ),
        "retrieved_context": ["chunk 1", "chunk 2"],
        "query_used": "Haircut recommendations for male ...",
    }


@pytest.fixture
def happy_mocks(monkeypatch, round_male_features):
    """Mock every external boundary so the pipeline runs offline."""
    monkeypatch.setattr(
        pipeline, "validate_index_exists", lambda: ValidationResult(True)
    )
    monkeypatch.setattr(pipeline, "handle_text", lambda text: round_male_features)
    monkeypatch.setattr(pipeline, "handle_image", lambda path: round_male_features)
    monkeypatch.setattr(pipeline, "check_same_person", lambda paths: (True, ""))
    monkeypatch.setattr(pipeline, "recommend", lambda features: _recommendation())


# ── HAPPY PATH ───────────────────────────────────────────────────────────────

def test_happy_path_text_only(happy_mocks):
    result = run_pipeline(user_text="I have a round face and curly thick hair. Male.")

    assert result.success
    assert result.error == ""
    assert result.input_sources == ["text"]
    assert result.features.face_shape == "Round"
    # The contract the card UI depends on:
    assert len(result.recommendation.haircuts) == 2
    for cut in result.recommendation.haircuts:
        assert cut.name and cut.why_it_works and cut.styling_tip and cut.maintenance
    assert result.recommendation.style_to_avoid == "Bowl Cut"
    assert result.retrieved_context  # RAG grounding present


def test_happy_path_image_plus_text(happy_mocks, fake_jpeg_bytes):
    result = run_pipeline(
        image_bytes=fake_jpeg_bytes,
        image_filename="selfie.jpg",
        user_text="Round face, curly thick hair, male here.",
    )
    assert result.success
    assert result.input_sources == ["image", "text"]


# ── UNHAPPY PATHS (regression guards for the security layer) ────────────────

def test_no_input_rejected(happy_mocks):
    result = run_pipeline()
    assert not result.success
    assert "at least one" in result.error


def test_fake_image_rejected(happy_mocks):
    result = run_pipeline(image_bytes=b"not an image", image_filename="x.jpg")
    assert not result.success
    assert "valid image" in result.error


def test_short_text_rejected(happy_mocks):
    result = run_pipeline(user_text="hi")
    assert not result.success
    assert "too short" in result.error.lower()


def test_missing_index_stops_early(monkeypatch):
    monkeypatch.setattr(
        pipeline, "validate_index_exists",
        lambda: ValidationResult(False, "Knowledge base index not found."),
    )
    result = run_pipeline(user_text="Round face, curly thick hair, male.")
    assert not result.success
    assert "index" in result.error.lower()


def test_gender_mismatch_between_photo_and_text(monkeypatch, fake_jpeg_bytes):
    """Photo says Male, description says Female → pipeline must refuse."""
    male = FaceFeatures(
        face_shape="Round", hair_type="Curly", hair_texture="Thick", gender="Male"
    )
    female = FaceFeatures(
        face_shape="Round", hair_type="Curly", hair_texture="Thick", gender="Female"
    )
    monkeypatch.setattr(
        pipeline, "validate_index_exists", lambda: ValidationResult(True)
    )
    monkeypatch.setattr(pipeline, "handle_image", lambda path: male)
    monkeypatch.setattr(pipeline, "handle_text", lambda text: female)

    result = run_pipeline(
        image_bytes=fake_jpeg_bytes,
        image_filename="selfie.jpg",
        user_text="I am female with a round face and curly hair.",
    )
    assert not result.success
    assert "gender" in result.error.lower() or "Female" in result.error
