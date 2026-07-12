"""
Service layer — routes input to the correct handler and runs the RAG pipeline.
UI layer calls only this file. No Streamlit imports here.
"""

import os
import tempfile
from pathlib import Path
from dataclasses import dataclass, field

from vision.feature_extractor import FaceFeatures, merge_features
from rag.recommender import recommend
from services.validator import (
    validate_image, validate_video, validate_text,
    validate_index_exists
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
    input_sources: list = field(default_factory=list)
    error: str = ""


def run_pipeline(
    image_bytes: bytes = None,
    image_filename: str = None,
    video_bytes: bytes = None,
    video_filename: str = None,
    user_text: str = None,
) -> PipelineResult:

    if not image_bytes and not video_bytes and not user_text:
        return PipelineResult(success=False, error="Please provide at least one of: image, video, or description.")

    # Validate knowledge base exists
    idx_check = validate_index_exists()
    if not idx_check.valid:
        return PipelineResult(success=False, error=idx_check.error)

    try:
        # Extract features from every input provided, in priority order
        # (image > video > text) so merge_features breaks ties consistently.
        candidates: list[FaceFeatures] = []
        input_sources: list[str] = []

        if image_bytes:
            check = validate_image(image_bytes, image_filename)
            if not check.valid:
                return PipelineResult(success=False, error=check.error)
            candidates.append(_run_with_tempfile(image_bytes, image_filename, handle_image))
            input_sources.append("image")

        if video_bytes:
            check = validate_video(video_bytes, video_filename)
            if not check.valid:
                return PipelineResult(success=False, error=check.error)
            candidates.append(_run_with_tempfile(video_bytes, video_filename, handle_video))
            input_sources.append("video")

        if user_text:
            check = validate_text(user_text)
            if not check.valid:
                return PipelineResult(success=False, error=check.error)
            candidates.append(handle_text(user_text))
            input_sources.append("text")

        features = merge_features(candidates)

        # ── RAG PIPELINE ──────────────────────────────────────────────
        result = recommend(features)

        return PipelineResult(
            success=True,
            features=features,
            recommendation=result["recommendation"],
            retrieved_context=result["retrieved_context"],
            query_used=result["query_used"],
            input_sources=input_sources,
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
