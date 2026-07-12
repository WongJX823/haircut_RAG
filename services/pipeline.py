"""
Service layer — routes input to the correct handler and runs the RAG pipeline.
UI layer calls only this file. No Streamlit imports here.
"""

import os
import tempfile
from pathlib import Path
from dataclasses import dataclass, field

from vision.feature_extractor import FaceFeatures, merge_features, check_same_person
from rag.recommender import recommend
from services.validator import (
    validate_image, validate_video, validate_text,
    validate_index_exists
)
from services.image_handler import handle_image
from services.video_handler import extract_frame_to_tempfile
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
    on_progress=None,
) -> PipelineResult:

    def progress(message: str):
        if on_progress:
            on_progress(message)

    if not image_bytes and not video_bytes and not user_text:
        return PipelineResult(success=False, error="Please provide at least one of: image, video, or description.")

    # Validate knowledge base exists
    idx_check = validate_index_exists()
    if not idx_check.valid:
        return PipelineResult(success=False, error=idx_check.error)

    image_tmp_path = None
    video_frame_tmp_path = None

    try:
        if image_bytes:
            check = validate_image(image_bytes, image_filename)
            if not check.valid:
                return PipelineResult(success=False, error=check.error)
            image_tmp_path = _write_tempfile(image_bytes, image_filename)

        if video_bytes:
            check = validate_video(video_bytes, video_filename)
            if not check.valid:
                return PipelineResult(success=False, error=check.error)
            progress("🎥 Extracting the sharpest frame from your video...")
            video_tmp_path = _write_tempfile(video_bytes, video_filename)
            try:
                video_frame_tmp_path = extract_frame_to_tempfile(video_tmp_path)
            finally:
                os.unlink(video_tmp_path)

        # If both a photo and a video frame are available, verify they show the
        # same person before spending effort recommending for the wrong face.
        if image_tmp_path and video_frame_tmp_path:
            progress("🔍 Checking that your photo and video show the same person...")
            same_person, reason = check_same_person([image_tmp_path, video_frame_tmp_path])
            if not same_person:
                return PipelineResult(
                    success=False,
                    error=(
                        "The uploaded photo and video don't appear to show the same person. "
                        + reason
                    ).strip(),
                )

        # Extract features from every input provided, in priority order
        # (image > video > text) so merge_features breaks ties consistently.
        candidates: list[FaceFeatures] = []
        input_sources: list[str] = []

        if image_tmp_path:
            progress("📷 Analysing your photo with GPT-4o Vision...")
            candidates.append(handle_image(image_tmp_path))
            input_sources.append("image")

        if video_frame_tmp_path:
            progress("🎥 Analysing your video frame with GPT-4o Vision...")
            candidates.append(handle_image(video_frame_tmp_path))
            input_sources.append("video")

        if user_text:
            check = validate_text(user_text)
            if not check.valid:
                return PipelineResult(success=False, error=check.error)
            progress("✏️ Parsing your written description...")
            candidates.append(handle_text(user_text))
            input_sources.append("text")

        # If a text description was given alongside a photo/video, make sure it
        # isn't describing a clearly different person. Gender is the clearest,
        # least subjective signal for this (face shape/hair can vary legitimately
        # between a photo and a self-description).
        visual_genders = {
            c.gender for src, c in zip(input_sources, candidates) if src in ("image", "video")
        }
        text_gender = next(
            (c.gender for src, c in zip(input_sources, candidates) if src == "text"), None
        )
        known_visual_genders = visual_genders - {"Unspecified"}
        if text_gender and text_gender != "Unspecified" and len(known_visual_genders) == 1:
            visual_gender = next(iter(known_visual_genders))
            if text_gender != visual_gender:
                return PipelineResult(
                    success=False,
                    error=(
                        f"Your description says gender is '{text_gender}', but the photo/video "
                        f"suggests '{visual_gender}'. Please make sure all inputs describe the same person."
                    ),
                )

        if len(candidates) > 1:
            progress("🧩 Combining features from all your inputs...")
        features = merge_features(candidates)

        # ── RAG PIPELINE ──────────────────────────────────────────────
        progress("📚 Searching the haircut knowledge base and writing your recommendation...")
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

    finally:
        for path in (image_tmp_path, video_frame_tmp_path):
            if path and os.path.exists(path):
                os.unlink(path)


def _write_tempfile(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(file_bytes)
        return tmp.name
