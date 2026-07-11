"""
Builds a query from face features, retrieves relevant chunks,
and generates a grounded haircut recommendation using GPT-4o.
"""

from openai import OpenAI
from vision.feature_extractor import FaceFeatures
from rag.retriever import retrieve_chunks
from prompts.rag_prompt import build_rag_prompt


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
        max_tokens=600,
    )

    return {
        "recommendation": response.choices[0].message.content,
        "retrieved_context": chunks,
        "query_used": query,
    }
