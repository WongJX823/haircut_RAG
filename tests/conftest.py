"""
Shared pytest setup.
Adds the project root to sys.path so tests can import services/, rag/, vision/
exactly like the app does, and provides reusable fixtures.
"""

import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from vision.feature_extractor import FaceFeatures  # noqa: E402


@pytest.fixture
def round_male_features() -> FaceFeatures:
    """The profile used across the happy-path tests."""
    return FaceFeatures(
        face_shape="Round", hair_type="Curly", hair_texture="Thick", gender="Male"
    )


@pytest.fixture
def fake_jpeg_bytes() -> bytes:
    """Minimal bytes that pass the JPEG magic-bytes check."""
    return b"\xff\xd8\xff" + b"\x00" * 100


@pytest.fixture
def chdir_project_root(monkeypatch):
    """Run a test from the project root (style_images uses relative paths)."""
    monkeypatch.chdir(PROJECT_ROOT)
