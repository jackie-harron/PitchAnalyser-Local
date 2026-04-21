"""
PitchAnalyser Local - Main Orchestration Script
Analyses video pitches and pitch decks locally using Ollama + Qwen2-VL
"""

import os
import json
import argparse
import time
from pathlib import Path
from typing import Optional
from pitchanalyser.extractor import extract_frames_from_video, extract_pages_from_deck
from pitchanalyser.scorer import score_pitch
from pitchanalyser.reporter import generate_report

DEFAULT_RUBRIC = {
    "problem_clarity": {
        "description": "How clearly is the problem/pain point defined? Is it compelling?",
        "weight": 1.0,
    },
    "solution_viability": {
        "description": "Is the proposed solution practical, innovative, and well-explained?",
        "weight": 1.0,
    },
    "market_opportunity": {
        "description": "Is the target market clearly defined? Is the market size credible and significant?",
        "weight": 1.0,
    },
    "business_model": {
        "description": "Is there a clear, believable path to revenue and profitability?",
        "weight": 1.0,
    },
    "traction_evidence": {
        "description": "Is there evidence of validation — users, revenue, pilots, letters of intent?",
        "weight": 1.0,
    },
    "team_credibility": {
        "description": "Does the team have relevant experience and capability to execute?",
        "weight": 1.0,
    },
    "competitive_advantage": {
        "description": "Is there a defensible moat or unfair advantage over competitors?",
        "weight": 1.0,
    },
    "presentation_quality": {
        "description": "Is the pitch clear, well-structured, and professionally delivered?",
        "weight": 0.75,
    },
    "financials_clarity": {
        "description": "Are financial projections realistic, well-reasoned, and clearly presented?",
        "weight": 0.75,
    },
    "ask_clarity": {
        "description": "Is the funding ask clear, with a specific use of funds and milestones?",
        "weight": 0.5,
    },
}


def load_rubric(rubric_path: Optional[str]) -> dict:
    if rubric_path and os.path.exists(rubric_path):
        with open(rubric_path) as f:
            return json.load(f)
    return DEFAULT_RUBRIC


def find_pitch_files(pitch_dir: str) -> list[dict]:
    """Find all pitch files (videos + decks), grouped by pitch name."""
    pitch_dir = Path(pitch_dir)
    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    deck_exts = {".pdf", ".pptx", ".ppt"}

    pitches = {}

    for f in pitch_dir.iterdir():
        if f.is_file():
            stem = f.stem
            ext = f.suffix.lower()
            if stem not in pitches:
                pitches[stem] = {"name": stem, "video": None, "deck": None}
            if ext in video_exts:
                pitches[stem]["video"] = str(f)
            elif ext in deck_exts:
                pitches[stem]["deck"] = str(f)

    # Filter out entries with no usable file
    valid = [p for p in pitches.values() if p["video"] or p["deck"]]
    return valid


def analyse_pitch(
    pitch: dict, rubric: dict, model: str, frames_per_minute: int, output_dir: str
) -> dict:
    name = pitch["name"]
    print(f"\n{'=' * 60}")
    print(f"  Analysing: {name}")
    print(f"{'=' * 60}")

    images = []
    sources_used = []

    # Extract frames from video
    if pitch["video"]:
        print(f"  [1/3] Extracting frames from video: {pitch['video']}")
        frames = extract_frames_from_video(
            pitch["video"],
            output_dir=os.path.join(output_dir, "frames", name),
            frames_per_minute=frames_per_minute,
        )
        images.extend(frames)
        sources_used.append(f"Video ({len(frames)} frames extracted)")
        print(f"        → {len(frames)} frames extracted")
    else:
        print("  [1/3] No video found, skipping frame extraction.")

    # Extract pages from deck
    if pitch["deck"]:
        print(f"  [2/3] Extracting pages from deck: {pitch['deck']}")
        pages = extract_pages_from_deck(
            pitch["deck"], output_dir=os.path.join(output_dir, "pages", name)
        )
        images.extend(pages)
        sources_used.append(f"Deck ({len(pages)} pages extracted)")
        print(f"        → {len(pages)} pages extracted")
    else:
        print("  [2/3] No deck found, skipping page extraction.")

    if not images:
        print(f"  ERROR: No images extracted for {name}. Skipping.")
        return None

    print(f"  [3/3] Scoring pitch with model '{model}'...")
    start = time.time()
    result = score_pitch(pitch_name=name, images=images, rubric=rubric, model=model)
    elapsed = time.time() - start
    print(f"        → Scored in {elapsed:.1f}s")
    result["sources"] = sources_used
    return result


def main():
    parser = argparse.ArgumentParser(description="PitchAnalyser Local — analyse startup pitches with a local AI model")
    parser.add_argument(
        "pitch_dir", help="Directory containing pitch files (videos and/or decks)"
    )
    parser.add_argument(
        "--rubric", help="Path to custom rubric JSON file", default=None
    )
    parser.add_argument("--model", help="Ollama model to use", default="qwen2.5vl")
    parser.add_argument(
        "--frames-per-minute",
        type=int,
        default=2,
        help="Video frames to extract per minute (default: 2)",
    )
    parser.add_argument(
        "--output-dir", help="Output directory for results", default="./pitch_results"
    )
    parser.add_argument(
        "--format",
        choices=["json", "html", "both"],
        default="both",
        help="Output format",
    )
    args = parser.parse_args()

    print("\n╔══════════════════════════════════════╗")
    print("║     LOCAL PITCH ANALYSER v1.0        ║")
    print("╚══════════════════════════════════════╝\n")

    # Setup
    os.makedirs(args.output_dir, exist_ok=True)
    rubric = load_rubric(args.rubric)
    print(f"  Model:    {args.model}")
    print(f"  Rubric:   {len(rubric)} criteria loaded")
    print(f"  Output:   {args.output_dir}")

    # Find pitches
    pitches = find_pitch_files(args.pitch_dir)
    if not pitches:
        print("\n  ERROR: No pitch files found in directory.")
        return

    print(f"\n  Found {len(pitches)} pitch(es):")
    for p in pitches:
        v = "✓ video" if p["video"] else "✗ video"
        d = "✓ deck" if p["deck"] else "✗ deck"
        print(f"    • {p['name']:<30} {v}  {d}")

    # Analyse each pitch
    results = []
    for pitch in pitches:
        result = analyse_pitch(
            pitch=pitch,
            rubric=rubric,
            model=args.model,
            frames_per_minute=args.frames_per_minute,
            output_dir=args.output_dir,
        )
        if result:
            results.append(result)

    if not results:
        print("\n  ERROR: No pitches could be analysed.")
        return

    # Generate report
    print(f"\n{'=' * 60}")
    print("  Generating report...")
    generate_report(
        results=results, rubric=rubric, output_dir=args.output_dir, fmt=args.format
    )

    print(f"\n  ✅ Done! Results saved to: {args.output_dir}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
