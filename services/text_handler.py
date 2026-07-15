"""
Handles text input — user describes their own features in plain English.
GPT-4o parses the description into structured FaceFeatures, then RAG runs as normal.
Skips the Vision module entirely.
"""

import json
from openai import OpenAI
from vision.feature_extractor import FaceFeatures

TEXT_PARSE_PROMPT = """
You are a hairstylist assistant. The user has described their physical features in plain text.
Extract the following information and return ONLY a JSON object:

{
  "face_shape": "<Oval | Round | Square | Heart>",
  "hair_type": "<Straight | Wavy | Curly | Coily>",
  "hair_texture": "<Fine | Medium | Thick>",
  "gender": "<Male | Female>",
  "gender_confidence": <number between 0.0 and 1.0>
}

Rules:
- Choose exactly one value per key from the options given (gender_confidence is a number, not a category).
- If the user does not mention a field, make a reasonable default:
    face_shape → "Oval", hair_type → "Straight", hair_texture → "Medium"
- For "gender": infer it from explicit statements ("I am male/female"), pronouns, or names.
  Always choose Male or Female — there is no "Unspecified" option.
- Set "gender_confidence" to 1.0 when the text is explicit about gender, and lower (down to 0.5)
  when you're guessing from weak cues, when nothing in the text indicates a gender at all, or
  when the text describes an androgynous/bigender presentation.
- Do not include anything outside the JSON.

User description:
"""


def handle_text(user_text: str) -> FaceFeatures:
    if not user_text or len(user_text.strip()) < 5:
        raise ValueError("Please provide a more detailed description of your features.")

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",        # cheaper model — no image needed here
        messages=[
            {"role": "user", "content": TEXT_PARSE_PROMPT + user_text}
        ],
        response_format={"type": "json_object"},
        max_tokens=150,
    )

    data = json.loads(response.choices[0].message.content)
    return FaceFeatures(**data)
