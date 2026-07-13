# HaircutAI — Multimodal RAG haircut recommender

Streamlit UI + GPT-4o Vision + FAISS RAG. 3-layer architecture:

- `app/main.py` — presentation only (Streamlit). No business logic here.
- `services/` — service layer: pipeline orchestration, validation, handlers. No Streamlit imports.
- `rag/`, `vision/`, `prompts/` — infrastructure: FAISS retrieval, GPT-4o calls, prompt templates.
- `tests/` — pytest suite. All OpenAI/FAISS calls are mocked; runs offline with no API key.

## Testing policy (required)

After ANY change to code in `app/`, `services/`, `rag/`, `vision/`, or `prompts/`:

1. Run the test suite: `python -m pytest tests/`
2. If tests fail, fix the CODE and re-run until green. Only change a test if the
   test itself is wrong (e.g. it asserts outdated behaviour) — say so explicitly.
3. Do not report a task as done while tests are red.
4. New features need at least one new test; bug fixes need a regression test
   that would have caught the bug.

## Conventions

- Keep layers separated: UI never imports from `rag/` or `vision/` directly — only via `services/`.
- All input validation lives in `services/validator.py`.
- External calls (OpenAI, FAISS) must stay mockable: import them at module level
  so tests can monkeypatch (e.g. `services.pipeline.recommend`).
- Run the app with: `python -m streamlit run app/main.py`
- Rebuild the knowledge index with: `python -m rag.build_index` (needs OpenAI credits).
