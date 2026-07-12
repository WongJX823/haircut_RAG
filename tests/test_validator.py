import os
import pytest
from services import validator

JPEG_BYTES = b"\xff\xd8\xff" + b"\x00" * 100
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
NOT_AN_IMAGE = b"plain text, not an image" * 10


# ---------------------------------------------------------------- API key

def test_validate_api_key_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = validator.validate_api_key()
    assert not result.valid


def test_validate_api_key_wrong_prefix(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-key")
    result = validator.validate_api_key()
    assert not result.valid


def test_validate_api_key_valid(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
    result = validator.validate_api_key()
    assert result.valid


# ---------------------------------------------------------------- image

def test_validate_image_wrong_extension():
    result = validator.validate_image(JPEG_BYTES, "photo.gif")
    assert not result.valid


def test_validate_image_empty():
    result = validator.validate_image(b"", "photo.jpg")
    assert not result.valid


def test_validate_image_too_large():
    oversized = b"\xff\xd8\xff" + b"\x00" * (validator.MAX_IMAGE_SIZE_BYTES + 1)
    result = validator.validate_image(oversized, "photo.jpg")
    assert not result.valid


def test_validate_image_bad_magic_bytes():
    result = validator.validate_image(NOT_AN_IMAGE, "photo.jpg")
    assert not result.valid


def test_validate_image_valid_jpeg():
    result = validator.validate_image(JPEG_BYTES, "photo.jpg")
    assert result.valid


def test_validate_image_valid_png():
    result = validator.validate_image(PNG_BYTES, "photo.png")
    assert result.valid


# ---------------------------------------------------------------- video

def test_validate_video_wrong_extension():
    result = validator.validate_video(b"\x00" * 100, "clip.gif")
    assert not result.valid


def test_validate_video_empty():
    result = validator.validate_video(b"", "clip.mp4")
    assert not result.valid


def test_validate_video_too_large():
    oversized = b"\x00" * (validator.MAX_VIDEO_SIZE_BYTES + 1)
    result = validator.validate_video(oversized, "clip.mp4")
    assert not result.valid


def test_validate_video_valid():
    result = validator.validate_video(b"\x00" * 100, "clip.mp4")
    assert result.valid


# ---------------------------------------------------------------- text

def test_validate_text_too_short():
    assert not validator.validate_text("short").valid


def test_validate_text_too_long():
    assert not validator.validate_text("x" * 1001).valid


def test_validate_text_valid():
    assert validator.validate_text("I have a round face with curly thick hair.").valid


# ---------------------------------------------------------------- index

def test_validate_index_exists_missing(tmp_path):
    result = validator.validate_index_exists(str(tmp_path / "does_not_exist"))
    assert not result.valid


def test_validate_index_exists_present(tmp_path):
    (tmp_path / "index.faiss").write_bytes(b"x")
    (tmp_path / "index.pkl").write_bytes(b"x")
    result = validator.validate_index_exists(str(tmp_path))
    assert result.valid
