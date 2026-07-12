FROM python:3.12-slim

# libglib2.0-0 is required by opencv-python-headless at import time
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first so this layer is cached across code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Cloud Run injects PORT (defaults to 8080); fall back to 8501 for local runs.
# If the FAISS index wasn't baked into the image, build it once at startup
# (requires OPENAI_API_KEY to be set).
CMD ["sh", "-c", "test -f knowledge_base/index/index.faiss || python -m rag.build_index; exec python -m streamlit run app/main.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]
