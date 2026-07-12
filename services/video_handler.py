"""
Handles video input — extracts the clearest frame and passes it to image handler.
Strategy: sample frames at 10% intervals, pick the sharpest one (highest Laplacian variance).
"""

import os
import cv2
import tempfile
import numpy as np
from services.image_handler import handle_image
from vision.feature_extractor import FaceFeatures


def _sharpness_score(frame: np.ndarray) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def extract_best_frame(video_path: str, num_samples: int = 10) -> np.ndarray:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open video file.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        raise ValueError("Video has no frames.")

    # Sample frames evenly across the video
    sample_positions = [int(total_frames * i / num_samples) for i in range(1, num_samples)]

    best_frame = None
    best_score = -1

    for pos in sample_positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret:
            continue
        score = _sharpness_score(frame)
        if score > best_score:
            best_score = score
            best_frame = frame

    cap.release()

    if best_frame is None:
        raise ValueError("Could not extract any frames from the video.")

    return best_frame


def handle_video(tmp_video_path: str) -> FaceFeatures:
    best_frame = extract_best_frame(tmp_video_path)

    # Save best frame as a temp JPEG and pass to image handler
    tmp_frame_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp_frame_path = tmp.name

        cv2.imwrite(tmp_frame_path, best_frame)
        return handle_image(tmp_frame_path)

    finally:
        if tmp_frame_path and os.path.exists(tmp_frame_path):
            os.unlink(tmp_frame_path)
