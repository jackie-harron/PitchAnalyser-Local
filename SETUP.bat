@echo off
title PitchAnalyser Local — Setup
color 0A

echo.
echo  ============================================
echo    PITCHANALYSER LOCAL — First Time Setup
echo  ============================================
echo.
echo  This creates a self-contained Python environment
echo  in a folder called .venv — nothing is installed globally.
echo.

REM ── Check Python ──────────────────────────────
echo  [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python not found!
    echo  Please install Python 3.10 or later from:
    echo  https://www.python.org/downloads/
    echo  (Tick "Add Python to PATH" during install)
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version') do set PYVER=%%v
echo  Found Python %PYVER%  OK

REM ── Create virtual environment ─────────────────
echo  [2/4] Creating virtual environment (.venv)...
if exist ".venv\Scripts\python.exe" (
    echo  .venv already exists  OK
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo  ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  Virtual environment created  OK
)

REM ── Install Python packages ───────────────────
echo  [3/4] Installing Python packages...
echo  (This may take a few minutes on first run)
echo.
.venv\Scripts\pip install --upgrade pip --quiet
.venv\Scripts\pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo  ERROR: Failed to install packages.
    echo  Try running this script as Administrator.
    pause
    exit /b 1
)
echo  Packages installed  OK

REM ── Check ffmpeg ──────────────────────────────
echo  [4/4] Checking ffmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  NOTE: ffmpeg not found.
    echo  Video analysis will not work without it.
    echo  Easiest install: winget install ffmpeg
    echo  Or download from: https://ffmpeg.org/download.html
    echo.
) else (
    echo  ffmpeg OK
)

REM ── Check Ollama ──────────────────────────────
echo.
echo  Checking Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  NOTE: Ollama not found or not in PATH.
    echo  Download and install from: https://ollama.com
    echo  Then run: ollama pull qwen2.5vl
    echo.
) else (
    echo  Ollama found  OK
)

echo.
echo  ============================================
echo    Setup complete!
echo    Run START.bat to launch PitchAnalyser Local.
echo  ============================================
echo.
pause
