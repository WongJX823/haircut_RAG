from vision.feature_extractor import FaceFeatures, GENDER_CONFIDENCE_THRESHOLD


def build_rag_prompt(features: FaceFeatures, context: str) -> str:
    gender_line = f"Gender     : {features.gender} (confidence: {features.gender_confidence:.0%})"
    if features.gender_confidence < GENDER_CONFIDENCE_THRESHOLD:
        gender_line += (
            "\nNote: this presentation reads as androgynous/bigender — favor versatile, "
            "unisex-friendly styles rather than committing to one gendered convention."
        )

    return f"""
You are an expert hairstylist giving personalised haircut advice.
Use ONLY the knowledge provided below to make your recommendation.
Do not invent styles that are not mentioned in the context.

--- CUSTOMER PROFILE ---
Face Shape : {features.face_shape}
Hair Type  : {features.hair_type}
Hair Texture: {features.hair_texture}
{gender_line}

--- HAIRCUT KNOWLEDGE ---
{context}

--- TASK ---
Recommend 2-3 specific haircut styles that suit this person, plus one style to avoid.

Respond with JSON only, using exactly this structure:
{{
  "summary": "One or two friendly sentences introducing your recommendations",
  "haircuts": [
    {{
      "name": "Style name",
      "why_it_works": "Why this style suits their face shape, hair type, and texture",
      "styling_tip": "How to style it and which product to use",
      "maintenance": "How often to trim and the upkeep required"
    }}
  ],
  "style_to_avoid": "Name of one style to avoid",
  "avoid_reason": "Why they should avoid it"
}}

Base every field on the knowledge provided. Keep the tone friendly and professional.
"""
