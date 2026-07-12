"""
Persists user satisfaction feedback on recommendations.
Appends one row per response to a local CSV file.
Note: on Cloud Run the filesystem is ephemeral — feedback survives only for
the life of the instance. Swap this for a database/Sheets call if it matters.
"""

import csv
import os
from datetime import datetime, timezone

from vision.feature_extractor import FaceFeatures

FEEDBACK_FILE = "feedback.csv"

_HEADER = [
    "timestamp_utc", "satisfied", "input_sources",
    "face_shape", "hair_type", "hair_texture", "gender",
]


def save_feedback(
    satisfied: bool,
    features: FaceFeatures,
    input_sources: list,
    path: str = FEEDBACK_FILE,
) -> None:
    is_new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(_HEADER)
        writer.writerow([
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "yes" if satisfied else "no",
            "+".join(input_sources),
            features.face_shape,
            features.hair_type,
            features.hair_texture,
            features.gender,
        ])
