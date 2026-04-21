#!/bin/bash
# setup.sh — First-time setup for PitchAnalyser Local on macOS/Linux
# Creates a self-contained Python virtual environment (.venv) in this folder.

echo ""
echo "============================================"
echo "  PITCHANALYSER LOCAL — First Time Setup"
echo "============================================"
echo ""

# ── Check Python ──────────────────────────────────
echo "[1/4] Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo ""
    echo "ERROR: Python 3 not found."
    echo "Install it from: https://www.python.org/downloads/"
    echo "Or on macOS: brew install python3"
    exit 1
fi
PYVER=$(python3 --version)
echo "  Found $PYVER  ✓"

# ── Create virtual environment ────────────────────
echo "[2/4] Creating virtual environment (.venv)..."
python3 -m venv .venv
echo "  Virtual environment created  ✓"

# ── Install Python packages ───────────────────────
echo "[3/4] Installing Python packages..."
echo "  (May take a few minutes on first run)"
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet
echo "  Packages installed  ✓"

# ── Check ffmpeg ──────────────────────────────────
echo "[4/4] Checking ffmpeg..."
if command -v ffmpeg &>/dev/null; then
    echo "  ffmpeg found  ✓"
else
    echo ""
    echo "  NOTE: ffmpeg not found. Video analysis will not work."
    echo "  Install it:"
    echo "    macOS:  brew install ffmpeg"
    echo "    Ubuntu: sudo apt install ffmpeg"
    echo ""
fi

# ── Check Ollama ──────────────────────────────────
echo ""
echo "Checking Ollama..."
if command -v ollama &>/dev/null; then
    echo "  Ollama found  ✓"
    echo "  Tip: pull the AI model with: ollama pull qwen2.5vl"
else
    echo ""
    echo "  NOTE: Ollama not found."
    echo "  Download from: https://ollama.com"
    echo "  Then run: ollama pull qwen2.5vl"
    echo ""
fi

echo ""
echo "============================================"
echo "  Setup complete!"
echo "  Run ./start.sh to launch PitchAnalyser Local."
echo "============================================"
echo ""
