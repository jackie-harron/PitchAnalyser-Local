#!/bin/bash
# start.sh — Launch PitchAnalyser Local on macOS/Linux

echo ""
echo "============================================"
echo "  PITCHANALYSER LOCAL — Starting...
============================================"
echo ""

# ── Check .venv exists ────────────────────────────
if [ ! -f ".venv/bin/python" ]; then
    echo "ERROR: Virtual environment not found."
    echo "Please run ./setup.sh first."
    exit 1
fi

# ── Start Ollama if not already running ───────────
if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo "Starting Ollama in background..."
    ollama serve &>/dev/null &
    sleep 3
fi

echo "Launching app..."
echo "Your browser will open automatically."
echo "Press Ctrl+C to stop."
echo ""

# Open browser after short delay
(sleep 3 && open "http://localhost:8501" 2>/dev/null || xdg-open "http://localhost:8501" 2>/dev/null) &

# Start Streamlit using the venv's Python
.venv/bin/python -m streamlit run app.py \
    --server.port 8501 \
    --server.headless false \
    --browser.gatherUsageStats false \
    --server.maxUploadSize 2000
