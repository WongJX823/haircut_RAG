"""
Tests for rag/recommender.py with the OpenAI client and FAISS retrieval
mocked out — verifies prompt flow, JSON parsing, and the plain-text fallback
without spending a cent or needing an API key.
"""

import json
from types import SimpleNamespace

import rag.recommender as recommender
from rag.recommender import recommend, StructuredRecommendation

GOOD_JSON = json.dumps({
    "summary": "Your round face and thick curly hair open up great options!",
    "haircuts": [
        {
            "name": "Undercut",
            "why_it_works": "Short sides reduce width on a round face.",
            "styling_tip": "Curl cream on damp hair, air dry.",
            "maintenance": "Trim every 4 weeks.",
        },
        {
            "name": "French Crop",
            "why_it_works": "The fringe adds structure.",
            "styling_tip": "Light matte clay.",
            "maintenance": "Trim every 3-4 weeks.",
        },
    ],
    "style_to_avoid": "Bowl Cut",
    "avoid_reason": "Adds width at the widest point of a round face.",
})


class FakeOpenAI:
    """Stands in for the OpenAI client; returns a canned response and
    records the request so tests can inspect what was sent."""

    canned_content = GOOD_JSON
    last_kwargs = None

    def __init__(self):
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        FakeOpenAI.last_kwargs = kwargs
        message = SimpleNamespace(content=FakeOpenAI.canned_content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _patch(monkeypatch, content=GOOD_JSON):
    FakeOpenAI.canned_content = content
    monkeypatch.setattr(recommender, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        recommender, "retrieve_chunks",
        lambda query, k=4: ["chunk about undercuts", "chunk about crops"],
    )


def test_valid_json_becomes_structured_cards(monkeypatch, round_male_features):
    _patch(monkeypatch)
    result = recommend(round_male_features)

    rec = result["recommendation"]
    assert isinstance(rec, StructuredRecommendation)
    assert len(rec.haircuts) == 2
    assert rec.haircuts[0].name == "Undercut"
    assert rec.style_to_avoid == "Bowl Cut"
    assert result["retrieved_context"] == ["chunk about undercuts", "chunk about crops"]


def test_query_contains_profile(monkeypatch, round_male_features):
    _patch(monkeypatch)
    result = recommend(round_male_features)
    for term in ("male", "Round", "Curly", "Thick"):
        assert term in result["query_used"]


def test_prompt_grounded_in_retrieved_chunks(monkeypatch, round_male_features):
    _patch(monkeypatch)
    recommend(round_male_features)
    prompt = FakeOpenAI.last_kwargs["messages"][0]["content"]
    assert "chunk about undercuts" in prompt   # RAG context injected
    assert "Round" in prompt                    # profile injected
    assert FakeOpenAI.last_kwargs["response_format"] == {"type": "json_object"}


def test_invalid_json_falls_back_to_plain_text(monkeypatch, round_male_features):
    _patch(monkeypatch, content="Sorry, here is plain text advice instead.")
    rec = recommend(round_male_features)["recommendation"]
    assert rec.haircuts == []
    assert rec.summary.startswith("Sorry")


def test_wrong_shape_json_falls_back(monkeypatch, round_male_features):
    # Valid JSON but missing required keys → ValidationError → fallback
    _patch(monkeypatch, content=json.dumps({"advice": "get a trim"}))
    rec = recommend(round_male_features)["recommendation"]
    assert rec.haircuts == []
