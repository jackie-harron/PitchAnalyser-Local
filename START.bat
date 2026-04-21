@echo off
title PitchAnalyser Local
color 0B

echo.
echo  ============================================
echo    PITCHANALYSER LOCAL — Starting...
echo  ============================================
echo.

REM ── Check .venv exists ────────────────────────
if not exist ".venv\Scripts\python.exe" (
    echo  ERROR: Virtual environment not found.
    echo  Please run SETUP.bat first.
    pause
    exit /b 1
)

REM ── Check Ollama is running, start if not ─────
echo  Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo  Starting Ollama in background...
    start /min "" ollama serve
    timeout /t 4 /nobreak >nul
)

echo  Launching app...
echo  Your browser will open automatically.
echo  To stop the app, close this window.
echo.

REM Open browser after a short delay
start /b "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8501"

REM Start Streamlit using the venv's Python
.venv\Scripts\python -m streamlit run app.py --server.port 8501 --server.headless false --browser.gatherUsageStats false

pause
