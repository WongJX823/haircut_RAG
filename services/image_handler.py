"""
Handles image input — existing vision flow, extracted here as its own handler.
"""

from vision.feature_extractor import extract_features, FaceFeatures


def handle_image(tmp_path: str) -> FaceFeatures:
    return extract_features(tmp_path)
