@echo off
echo ========================================
echo   Enterprise RAG - Frontend Starter
echo ========================================

cd /d "%~dp0frontend"

IF NOT EXIST "node_modules" (
    echo Installing React packages (first time only - takes 2-3 mins)...
    npm install
)

echo.
echo Starting React frontend on http://localhost:3000
echo Press Ctrl+C to stop.
echo.
npm start
