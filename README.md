# ✂️ HaircutAI

A multimodal RAG (Retrieval-Augmented Generation) app that recommends a personalised haircut based on your face shape, hair type, and hair texture — detected from a photo, a short video, a written description, or any combination of the three.

## How it works

1. **Input** — provide any combination of:
   - 📷 a front-facing photo (JPG/PNG/WEBP)
   - 🎥 a short face video (MP4/MOV/AVI/MKV/WEBM) — the sharpest frame is extracted automatically
   - ✏️ a written description of your face and hair
2. **Feature extraction** — each input is analysed independently:
   - Photo/video frame → GPT-4o Vision → `face_shape`, `hair_type`, `hair_texture`, `gender`
   - Text → GPT-4o-mini parses the description into the same structured fields
3. **Merge** — if multiple inputs were given, the results are combined field-by-field by majority vote (ties broken in favour of image > video > text).
4. **Retrieval** — the merged profile is turned into a search query and matched against a FAISS vector index built from a local knowledge base of haircut guides.
5. **Recommendation** — GPT-4o generates a grounded recommendation using only the retrieved knowledge, citing which style to try and which to avoid.

See [diagrams/haircut_ai_diagrams.drawio](diagrams/haircut_ai_diagrams.drawio) for the full flowchart, use case, and data flow diagrams.

## Project structure

```
app/main.py              Streamlit UI (presentation layer only)
services/
  pipeline.py             Orchestrates validation → feature extraction → merge → RAG
  image_handler.py         Routes an image to the vision extractor
  video_handler.py         Extracts the sharpest frame from a video (OpenCV, Laplacian variance)
  text_handler.py          Parses a free-text description via GPT-4o-mini
  validator.py             Centralised input validation (file type/size, magic bytes, API key)
vision/feature_extractor.py  GPT-4o Vision call + merge_features() for combining multiple inputs
rag/
  build_index.py           Builds the FAISS index from knowledge_base/docs/*.txt
  retriever.py              Loads the index and retrieves relevant chunks
  recommender.py             Builds the query, retrieves chunks, calls GPT-4o for the recommendation
prompts/                  Prompt templates (vision + RAG)
knowledge_base/docs/      Haircut guides used as the RAG knowledge source
utils/scrape_article.py   CLI to scrape an article URL into the knowledge base
```

## Setup

**Prerequisites:** Python 3.10+ and an [OpenAI API key](https://platform.openai.com/api-keys).

1. Clone the repo and install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and add your key:
   ```
   OPENAI_API_KEY=sk-...
   ```
3. Build the knowledge base index (reads `knowledge_base/docs/*.txt`, embeds with OpenAI, saves a FAISS index):
   ```
   python -m rag.build_index
   ```
4. Run the app:
   ```
   python -m streamlit run app/main.py
   ```

### Windows shortcut

[run.bat](run.bat) collapses all of the above into one command — it checks Python is installed, installs dependencies if missing, builds the index if missing, then launches the app:

```
run.bat
```

## Running tests

```
pip install -r requirements-dev.txt
python -m pytest tests/
```

## Extending the knowledge base

Add more `.txt` guides to `knowledge_base/docs/`, or scrape an article directly:

```
python utils/scrape_article.py <URL> <output_filename.txt>
```

Then rebuild the index with `python -m rag.build_index`.
