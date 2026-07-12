@echo off
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python not found on PATH. Install it from python.org and check "Add python.exe to PATH".
    pause
    exit /b 1
)

if not exist ".env" (
    echo ERROR: .env file not found. Copy .env.example to .env and add your OPENAI_API_KEY.
    pause
    exit /b 1
)

python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies.
        pause
        exit /b 1
    )
)

if not exist "knowledge_base\index\index.faiss" (
    echo Building knowledge base index...
    python -m rag.build_index
    if errorlevel 1 (
        echo Failed to build index.
        pause
        exit /b 1
    )
)

echo Starting HaircutAI...
python -m streamlit run app\main.py
pause
