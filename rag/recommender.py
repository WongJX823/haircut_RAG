"""
Builds a query from face features, retrieves relevant chunks,
and generates a grounded haircut recommendation using GPT-4o.
The output is structured JSON validated with Pydantic so the UI
can render recommendation cards instead of a wall of text.
"""

import json

from openai import OpenAI
from pydantic import BaseModel, ValidationError
from vision.feature_extractor import FaceFeatures
from rag.retriever import retrieve_chunks
from prompts.rag_prompt import build_rag_prompt


class HaircutOption(BaseModel):
    name: str          # e.g. "Textured Crop"
    why_it_works: str  # why it suits this face shape / hair type
    styling_tip: str   # how to style it, which product to use
    maintenance: str   # trim frequency and upkeep


class StructuredRecommendation(BaseModel):
    summary: str
    haircuts: list[HaircutOption]
    style_to_avoid: str = ""
    avoid_reason: str = ""


def recommend(features: FaceFeatures) -> dict:
    query = (
        f"Haircut recommendations for {features.gender.lower()} with "
        f"{features.face_shape} face shape, {features.hair_type} hair, "
        f"{features.hair_texture} texture"
    )

    chunks = retrieve_chunks(query, k=4)
    context = "\n\n".join(chunks)
    prompt = build_rag_prompt(features, context)

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=900,
        response_format={"type": "json_object"},  # forces syntactically valid JSON
    )
    raw = response.choices[0].message.content

    try:
        recommendation = StructuredRecommendation(**json.loads(raw))
    except (json.JSONDecodeError, ValidationError):
        # If the model ever returns an unexpected shape, degrade gracefully
        # to a plain-text recommendation instead of crashing the pipeline.
        recommendation = StructuredRecommendation(summary=raw, haircuts=[])

    return {
        "recommendation": recommendation,
        "retrieved_context": chunks,
        "query_used": query,
    }
