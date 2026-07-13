"""
Persists user satisfaction feedback.
On Cloud Run: writes to Firestore (persistent across restarts).
Locally: falls back to a CSV file when ADC credentials are unavailable.
If a Firestore write fails at runtime, falls back to CSV automatically.
"""

import csv
import os
import traceback
from datetime import datetime, timezone

from vision.feature_extractor import FaceFeatures

FEEDBACK_FILE = "feedback.csv"
FIRESTORE_COLLECTION = "feedback"
_SUGGESTION_MAX = 500

_HEADER = [
    "timestamp_utc", "satisfied", "input_sources",
    "face_shape", "hair_type", "hair_texture", "gender",
    "suggestion",
]


def _sanitize_csv(value: str) -> str:
    """Prevent CSV formula injection when the file is opened in a spreadsheet."""
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def _firestore_client():
    """Returns a Firestore client using ADC, or None if unavailable."""
    try:
        from google.cloud import firestore
    except ImportError:
        return None
    try:
        return firestore.Client()
    except Exception:
        return None


def save_feedback(
    satisfied: bool,
    features: FaceFeatures,
    input_sources: list,
    suggestion: str = "",
    path: str = FEEDBACK_FILE,
) -> None:
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "satisfied": "yes" if satisfied else "no",
        "input_sources": "+".join(input_sources),
        "face_shape": features.face_shape,
        "hair_type": features.hair_type,
        "hair_texture": features.hair_texture,
        "gender": features.gender,
        "suggestion": suggestion.strip()[:_SUGGESTION_MAX],
    }

    db = _firestore_client()
    if db is not None:
        try:
            db.collection(FIRESTORE_COLLECTION).add(record)
            return
        except Exception:
            traceback.print_exc()

    _append_csv(record, path)


def _append_csv(record: dict, path: str) -> None:
    is_new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(_HEADER)
        writer.writerow([
            record["timestamp_utc"],
            record["satisfied"],
            record["input_sources"],
            record["face_shape"],
            record["hair_type"],
            record["hair_texture"],
            record["gender"],
            _sanitize_csv(record["suggestion"]),
        ])
