"""
Sends a facial image to GPT-4o Vision and returns structured face/hair features.
"""

import base64
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel
from prompts.vision_prompt import VISION_PROMPT


class FaceFeatures(BaseModel):
    face_shape: str       # Oval | Round | Square | Heart
    hair_type: str        # Straight | Wavy | Curly | Coily
    hair_texture: str     # Fine | Medium | Thick
    gender: str           # Male | Female | Unspecified


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
    import json
    data = json.loads(raw)
    return FaceFeatures(**data)
