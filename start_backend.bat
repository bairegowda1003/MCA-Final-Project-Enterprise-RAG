@echo off
echo ========================================
echo   Enterprise RAG - Backend Starter
echo ========================================
cd /d "%~dp0backend"
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing packages...
pip install -r requirements.txt --quiet
echo.
echo NOTE: Make sure backend/.env exists with your OPENROUTER_API_KEY
echo Starting FastAPI on http://localhost:8000 ...
uvicorn app:app --reload --port 8000
