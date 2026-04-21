# 🎯 PitchAnalyser Local — Quick Start Guide

Welcome! This guide will get you up and running in about 10 minutes.

---

## What you'll need to install (one time only)

### Step 1 — Install Python
1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python"** button
3. Run the installer
4. ⚠️ **Important:** Tick the box that says **"Add Python to PATH"** before clicking Install

### Step 2 — Install Ollama (the local AI)
1. Go to **https://ollama.com**
2. Click **Download** and install it like any normal app
3. Once installed, open a Terminal (Mac) or Command Prompt (Windows) and run:
   ```
   ollama pull qwen2.5vl
   ```
   This downloads the AI model (~5 GB). Only needed once.

### Step 3 — Install ffmpeg (for video support)
**Mac:**
- Install Homebrew from **https://brew.sh** if you don't have it
- Then run: `brew install ffmpeg`

**Windows (easiest):**
- Run: `winget install ffmpeg`
- Or download from **https://ffmpeg.org/download.html** (choose "Windows builds"), extract the zip and add the `bin` folder to your PATH

---

## First-time setup

This creates a self-contained Python environment (a folder called `.venv`) so that nothing is installed globally on your machine.

**Windows:**
1. Double-click **`SETUP.bat`**
2. Wait for it to finish (installs everything into `.venv`)

**Mac / Linux:**
1. Open Terminal in this folder
2. Run: `chmod +x setup.sh start.sh && ./setup.sh`

---

## Starting the app

**Every time you want to use PitchAnalyser Local:**

- **Windows:** Double-click **`START.bat`**
- **Mac/Linux:** Run `./start.sh` in Terminal

A browser window will open automatically at `http://localhost:8501`

---

## How to use it

### 1. Check the status panel (left sidebar)
Make sure you see green ticks for:
- ✅ Ollama Running
- ✅ Model Ready
- ✅ ffmpeg Found

### 2. Upload your pitches
- Click the **Upload & Analyse** tab
- Drag and drop your pitch files (videos and/or PDF/PPTX decks)
- Files with the **same name** (e.g. `CompanyA.mp4` + `CompanyA.pdf`) are automatically combined

### 3. Run the analysis
- Click **"Analyse All Pitches"**
- Wait while the AI processes each pitch (a few minutes per pitch)

### 4. View results
- Switch to the **Results** tab
- See the ranked leaderboard
- Click any pitch to see detailed scores and feedback
- Download the full HTML report or JSON data

### 5. Customise the rubric (optional)
- Go to the **Rubric Editor** tab
- Adjust criteria descriptions and weights for your competition
- Save your rubric as a JSON file to reuse next time

---

## Tips

- **Faster analysis:** Use fewer frames per minute (set to 1 in Settings)
- **Better analysis:** Keep videos under 20 minutes for best results
- **Custom rubric:** Load your saved `my_rubric.json` from the sidebar
- **The app is 100% private** — no internet connection is used during analysis

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Ollama not running" | Open the Ollama app, or run `ollama serve` in Terminal |
| "Model not pulled" | Run `ollama pull qwen2.5vl` in Terminal |
| Browser doesn't open | Manually go to `http://localhost:8501` |
| Videos not processing | Install ffmpeg (see Step 3 above) |
| App won't start | Re-run SETUP.bat / setup.sh |

---

*For more detail, see [README.md](README.md).*
