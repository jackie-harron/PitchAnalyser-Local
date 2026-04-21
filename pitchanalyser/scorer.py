"""
scorer.py - Score pitches against a rubric using a local Ollama vision model.
All inference runs locally. No data leaves the machine.
"""

import json
import requests
import time

OLLAMA_BASE_URL = "http://localhost:11434"


def check_ollama_running() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return resp.status_code == 200
    except requests.ConnectionError:
        return False


def check_model_available(model: str) -> bool:
    """Check if the specified model is pulled in Ollama."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            # Check for exact match or prefix match (e.g. "qwen2-vl" matches "qwen2-vl:latest")
            return any(m == model or m.startswith(model + ":") for m in models)
    except:
        pass
    return False


def build_rubric_prompt(rubric: dict) -> str:
    """Build the scoring prompt from the rubric definition."""
    criteria_text = "\n".join(
        [
            f"  - {key} (weight: {v['weight']}): {v['description']}"
            for key, v in rubric.items()
        ]
    )

    criteria_json = "\n".join(
        [
            f'    "{key}": {{"score": <1-10>, "justification": "<2-3 sentence explanation>"}}'
            for key in rubric.keys()
        ]
    )

    return f"""You are an expert startup investor and pitch evaluator. You will be shown frames from a startup pitch — either from a video presentation, a pitch deck, or both.

Your task is to evaluate this pitch against the following rubric criteria:

{criteria_text}

IMPORTANT INSTRUCTIONS:
1. Score each criterion from 1 to 10 (1=very poor, 5=average, 10=exceptional)
2. Base your scores ONLY on evidence visible in the provided images
3. Be objective and consistent — score as if you are comparing against all startup pitches you've seen
4. Provide a brief justification for each score (2-3 sentences)
5. Also provide an overall_summary (3-5 sentences about the pitch's key strengths and weaknesses)
6. Also provide a recommendation: one of "Strong Pass", "Pass", "Borderline", "Pass with Concerns", "No Pass"

Respond ONLY with valid JSON in this exact format (no preamble, no markdown, no explanation outside the JSON):

{{
  "scores": {{
{criteria_json}
  }},
  "overall_summary": "<3-5 sentence overall assessment>",
  "recommendation": "<Strong Pass|Pass|Borderline|Pass with Concerns|No Pass>",
  "key_strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "key_concerns": ["<concern 1>", "<concern 2>", "<concern 3>"]
}}"""


def score_pitch(
    pitch_name: str,
    images: list[str],
    rubric: dict,
    model: str = "qwen2.5vl",
    max_images: int = 20,
    retry_attempts: int = 3,
) -> dict:
    """
    Score a pitch against the rubric using a local Ollama vision model.

    Args:
        pitch_name: Name of the pitch (for labelling)
        images: List of base64-encoded images (frames + pages)
        rubric: Dict of rubric criteria
        model: Ollama model name to use
        max_images: Max images to send (to stay within context limits)
        retry_attempts: Number of retry attempts on failure

    Returns:
        Dict with pitch_name, scores, summary, recommendation, etc.
    """
    if not check_ollama_running():
        raise RuntimeError(
            "Ollama is not running!\n"
            "Start it with: ollama serve\n"
            "Or download from: https://ollama.com"
        )

    if not check_model_available(model):
        raise RuntimeError(
            f"Model '{model}' is not available in Ollama.\n"
            f"Pull it with: ollama pull {model}\n"
            f"Recommended models: qwen2.5vl, llava:7b, llama3.2-vision"
        )

    # Sample images evenly if we have more than max_images
    if len(images) > max_images:
        step = len(images) / max_images
        images = [images[int(i * step)] for i in range(max_images)]

    prompt = build_rubric_prompt(rubric)

    # Build the message content: text prompt + all images
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": images,  # Ollama expects base64 strings in a separate images list
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 2000,
        },
    }

    for attempt in range(retry_attempts):
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=300,  # 5 minute timeout for large models
            )
            response.raise_for_status()
            raw_text = response.json()["message"]["content"]
            scores = parse_score_response(raw_text, rubric)
            scores["pitch_name"] = pitch_name
            scores["images_analysed"] = len(images)
            return scores

        except requests.Timeout:
            print(
                f"    WARNING: Request timed out (attempt {attempt + 1}/{retry_attempts})"
            )
            time.sleep(5)
        except requests.HTTPError as e:
            print(
                f"    WARNING: HTTP error: {e} (attempt {attempt + 1}/{retry_attempts})"
            )
            time.sleep(5)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(
                f"    WARNING: Failed to parse response: {e} (attempt {attempt + 1}/{retry_attempts})"
            )
            time.sleep(2)

    # If all retries fail, return a placeholder result
    return {
        "pitch_name": pitch_name,
        "error": "Failed to score after all retry attempts",
        "scores": {
            k: {"score": 0, "justification": "Scoring failed"} for k in rubric.keys()
        },
        "overall_summary": "Scoring failed",
        "recommendation": "Unknown",
        "key_strengths": [],
        "key_concerns": ["Scoring failed — check Ollama logs"],
        "weighted_total": 0.0,
        "images_analysed": len(images),
    }


def parse_score_response(raw_text: str, rubric: dict) -> dict:
    """Parse and validate the JSON response from the model."""
    # Strip any markdown code fences if present
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last fence lines
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    data = json.loads(text)

    # Validate and normalise scores
    scores = data.get("scores", {})
    for key in rubric:
        if key not in scores:
            scores[key] = {"score": 5, "justification": "Not assessed"}
        else:
            # Clamp scores to 1-10
            scores[key]["score"] = max(1, min(10, int(scores[key].get("score", 5))))

    # Calculate weighted total score
    total_weight = sum(v["weight"] for v in rubric.values())
    weighted_sum = sum(
        scores.get(k, {}).get("score", 0) * v["weight"] for k, v in rubric.items()
    )
    weighted_total = (weighted_sum / total_weight) if total_weight > 0 else 0.0

    return {
        "scores": scores,
        "overall_summary": data.get("overall_summary", ""),
        "recommendation": data.get("recommendation", "Unknown"),
        "key_strengths": data.get("key_strengths", []),
        "key_concerns": data.get("key_concerns", []),
        "weighted_total": round(weighted_total, 2),
    }
