"""
Service layer — routes input to the correct handler and runs the RAG pipeline.
UI layer calls only this file. No Streamlit imports here.
"""

import os
import tempfile
from pathlib import Path
from dataclasses import dataclass, field

from vision.feature_extractor import FaceFeatures
from rag.recommender import recommend
from services.validator import (
    validate_image, validate_video, validate_text,
    validate_index_exists, get_input_type
)
from services.image_handler import handle_image
from services.video_handler import handle_video
from services.text_handler import handle_text


@dataclass
class PipelineResult:
    success: bool
    features: FaceFeatures = None
    recommendation: str = ""
    retrieved_context: list = field(default_factory=list)
    query_used: str = ""
    input_type: str = ""
    error: str = ""


def run_pipeline(
    input_type: str,
    file_bytes: bytes = None,
    filename: str = None,
    user_text: str = None,
) -> PipelineResult:

    # Validate knowledge base exists for all input types
    idx_check = validate_index_exists()
    if not idx_check.valid:
        return PipelineResult(success=False, error=idx_check.error)

    try:
        # ── TEXT INPUT ──────────────────────────────────────────────
        if input_type == "text":
            check = validate_text(user_text)
            if not check.valid:
                return PipelineResult(success=False, error=check.error)
            features = handle_text(user_text)

        # ── IMAGE INPUT ─────────────────────────────────────────────
        elif input_type == "image":
            check = validate_image(file_bytes, filename)
            if not check.valid:
                return PipelineResult(success=False, error=check.error)
            features = _run_with_tempfile(file_bytes, filename, handle_image)

        # ── VIDEO INPUT ─────────────────────────────────────────────
        elif input_type == "video":
            check = validate_video(file_bytes, filename)
            if not check.valid:
                return PipelineResult(success=False, error=check.error)
            features = _run_with_tempfile(file_bytes, filename, handle_video)

        else:
            return PipelineResult(success=False, error=f"Unknown input type: {input_type}")

        # ── RAG PIPELINE (same for all input types) ─────────────────
        result = recommend(features)

        return PipelineResult(
            success=True,
            features=features,
            recommendation=result["recommendation"],
            retrieved_context=result["retrieved_context"],
            query_used=result["query_used"],
            input_type=input_type,
        )

    except Exception as e:
        return PipelineResult(success=False, error=f"Pipeline error: {str(e)}")


def _run_with_tempfile(file_bytes: bytes, filename: str, handler_fn) -> FaceFeatures:
    ext = Path(filename).suffix.lower()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        return handler_fn(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
