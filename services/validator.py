"""
Input validation and security checks.
All validation lives here — nothing else should validate inputs.
"""

import os
from dataclasses import dataclass

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS

MAX_IMAGE_SIZE_MB = 5
MAX_VIDEO_SIZE_MB = 50
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024


@dataclass
class ValidationResult:
    valid: bool
    error: str = ""


def validate_api_key() -> ValidationResult:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        return ValidationResult(False, "OPENAI_API_KEY is not set. Add it to your .env file.")
    if not key.startswith("sk-"):
        return ValidationResult(False, "OPENAI_API_KEY looks invalid. It should start with 'sk-'.")
    return ValidationResult(True)


def get_input_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    if ext in ALLOWED_VIDEO_EXTENSIONS:
        return "video"
    return "unknown"


def validate_image(file_bytes: bytes, filename: str) -> ValidationResult:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return ValidationResult(
            False,
            f"File type '{ext}' not allowed. Please upload a JPG, PNG, or WEBP image."
        )

    size = len(file_bytes)
    if size == 0:
        return ValidationResult(False, "Uploaded file is empty.")
    if size > MAX_IMAGE_SIZE_BYTES:
        mb = size / (1024 * 1024)
        return ValidationResult(
            False,
            f"File too large ({mb:.1f} MB). Maximum image size is {MAX_IMAGE_SIZE_MB} MB."
        )

    # Magic bytes check — verify actual file signature
    jpeg_sig = file_bytes[:3] == b"\xff\xd8\xff"
    png_sig  = file_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    webp_sig = file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP"

    if not (jpeg_sig or png_sig or webp_sig):
        return ValidationResult(
            False,
            "File does not appear to be a valid image. Please upload a real JPG, PNG, or WEBP."
        )
    return ValidationResult(True)


def validate_video(file_bytes: bytes, filename: str) -> ValidationResult:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        return ValidationResult(
            False,
            f"File type '{ext}' not allowed. Please upload an MP4, MOV, or AVI video."
        )

    size = len(file_bytes)
    if size == 0:
        return ValidationResult(False, "Uploaded video is empty.")
    if size > MAX_VIDEO_SIZE_BYTES:
        mb = size / (1024 * 1024)
        return ValidationResult(
            False,
            f"Video too large ({mb:.1f} MB). Maximum video size is {MAX_VIDEO_SIZE_MB} MB."
        )
    return ValidationResult(True)


def validate_text(text: str) -> ValidationResult:
    if not text or len(text.strip()) < 10:
        return ValidationResult(
            False,
            "Description too short. Please describe your face shape, hair type, and texture."
        )
    if len(text) > 1000:
        return ValidationResult(False, "Description too long. Please keep it under 1000 characters.")
    return ValidationResult(True)


def validate_index_exists(index_dir: str = "knowledge_base/index") -> ValidationResult:
    faiss_file = os.path.join(index_dir, "index.faiss")
    pkl_file   = os.path.join(index_dir, "index.pkl")
    if not os.path.exists(faiss_file) or not os.path.exists(pkl_file):
        return ValidationResult(
            False,
            "Knowledge base index not found. Run: python -m rag.build_index"
        )
    return ValidationResult(True)
