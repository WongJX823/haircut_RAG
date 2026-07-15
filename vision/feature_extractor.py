"""
Sends a facial image to GPT-4o Vision and returns structured face/hair features.
"""

import base64
import json
from collections import Counter
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel, Field
from prompts.vision_prompt import VISION_PROMPT, SAME_PERSON_PROMPT


# Below this, a gender read is treated as an androgynous/bigender coin-flip
# rather than a confident Male/Female call (used by pipeline/RAG/style lookup).
GENDER_CONFIDENCE_THRESHOLD = 0.65


class FaceFeatures(BaseModel):
    face_shape: str            # Oval | Round | Square | Heart
    hair_type: str             # Straight | Wavy | Curly | Coily
    hair_texture: str          # Fine | Medium | Thick
    gender: str                # Male | Female
    gender_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    # 1.0 = clearly one presentation, scaling down toward 0.5 for an
    # androgynous/bigender presentation where the Male/Female pick is a coin flip.


def merge_features(candidates: list[FaceFeatures]) -> FaceFeatures:
    """
    Combines features extracted from multiple inputs (e.g. image + video + text)
    into one profile. Per field, takes the majority value; ties go to whichever
    candidate appears first, so callers should order `candidates` by priority
    (most trustworthy source first, e.g. image before video before text).
    `gender_confidence` is numeric, not categorical, so it's averaged instead.
    """
    if not candidates:
        raise ValueError("No feature candidates to merge.")
    if len(candidates) == 1:
        return candidates[0]

    merged = {}
    for field in FaceFeatures.model_fields:
        if field == "gender_confidence":
            merged[field] = sum(getattr(c, field) for c in candidates) / len(candidates)
            continue
        values = [getattr(c, field) for c in candidates]
        counts = Counter(values)
        top_count = max(counts.values())
        merged[field] = next(v for v in values if counts[v] == top_count)
    return FaceFeatures(**merged)


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_features(image_path: str) -> FaceFeatures:
    client = OpenAI()
    b64 = encode_image(image_path)
    ext = Path(image_path).suffix.lstrip(".").lower()
    media_type = "jpeg" if ext in ("jpg", "jpeg") else ext

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/{media_type};base64,{b64}"},
                    },
                ],
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=300,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    return FaceFeatures(**data)


def check_same_person(image_paths: list[str]) -> tuple[bool, str]:
    """
    Sends 2+ face images to GPT-4o Vision and asks whether they depict the
    same person. Used to catch mismatched inputs (e.g. a photo and a video
    of two different people) before generating a recommendation.
    """
    client = OpenAI()
    content = [{"type": "text", "text": SAME_PERSON_PROMPT}]
    for path in image_paths:
        b64 = encode_image(path)
        ext = Path(path).suffix.lstrip(".").lower()
        media_type = "jpeg" if ext in ("jpg", "jpeg") else ext
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/{media_type};base64,{b64}"},
        })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"},
        max_tokens=150,
    )

    data = json.loads(response.choices[0].message.content)
    return bool(data.get("same_person", True)), data.get("reason", "")
