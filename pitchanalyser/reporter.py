"""
reporter.py - Generate ranked reports from pitch scoring results.
Outputs JSON and/or a standalone HTML report.
"""

import json
import os
from datetime import datetime


RECOMMENDATION_COLORS = {
    "Strong Pass": "#22c55e",
    "Pass": "#84cc16",
    "Borderline": "#f59e0b",
    "Pass with Concerns": "#f97316",
    "No Pass": "#ef4444",
    "Unknown": "#94a3b8",
}

RECOMMENDATION_EMOJI = {
    "Strong Pass": "🟢",
    "Pass": "🟡",
    "Borderline": "🟠",
    "Pass with Concerns": "🟠",
    "No Pass": "🔴",
    "Unknown": "⚪",
}


def rank_results(results: list[dict]) -> list[dict]:
    """Sort results by weighted total score, descending."""
    return sorted(results, key=lambda r: r.get("weighted_total", 0), reverse=True)


def generate_report(
    results: list[dict], rubric: dict, output_dir: str, fmt: str = "both"
):
    """Generate ranked output report(s)."""
    ranked = rank_results(results)

    # Attach rank to each result
    for i, r in enumerate(ranked):
        r["rank"] = i + 1

    if fmt in ("json", "both"):
        _write_json(ranked, rubric, output_dir)

    if fmt in ("html", "both"):
        _write_html(ranked, rubric, output_dir)

    # Print summary to console
    _print_summary(ranked)


def _write_json(ranked: list[dict], rubric: dict, output_dir: str):
    output = {
        "generated_at": datetime.now().isoformat(),
        "rubric_criteria": list(rubric.keys()),
        "total_pitches": len(ranked),
        "rankings": ranked,
    }
    path = os.path.join(output_dir, "results.json")
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  📄 JSON results saved: {path}")


def _write_html(ranked: list[dict], rubric: dict, output_dir: str):
    criteria_keys = list(rubric.keys())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Build radar chart data for each pitch
    radar_datasets = []
    colors = [
        "rgba(99,102,241,0.7)",
        "rgba(16,185,129,0.7)",
        "rgba(245,158,11,0.7)",
        "rgba(239,68,68,0.7)",
        "rgba(14,165,233,0.7)",
        "rgba(168,85,247,0.7)",
        "rgba(236,72,153,0.7)",
        "rgba(34,197,94,0.7)",
    ]
    for i, r in enumerate(ranked):
        scores_data = [
            r.get("scores", {}).get(k, {}).get("score", 0) for k in criteria_keys
        ]
        radar_datasets.append(
            {
                "label": r["pitch_name"],
                "data": scores_data,
                "borderColor": colors[i % len(colors)],
                "backgroundColor": colors[i % len(colors)].replace("0.7", "0.1"),
            }
        )

    # Build pitch cards HTML
    cards_html = ""
    for r in ranked:
        rec = r.get("recommendation", "Unknown")
        color = RECOMMENDATION_COLORS.get(rec, "#94a3b8")
        emoji = RECOMMENDATION_EMOJI.get(rec, "⚪")
        score = r.get("weighted_total", 0)
        sources = ", ".join(r.get("sources", ["Unknown"]))

        # Score bars for each criterion
        criteria_html = ""
        for k in criteria_keys:
            s = r.get("scores", {}).get(k, {})
            sc = s.get("score", 0)
            just = s.get("justification", "")
            pct = sc * 10
            bar_color = "#22c55e" if sc >= 7 else "#f59e0b" if sc >= 4 else "#ef4444"
            criteria_html += f"""
            <div class="criterion">
              <div class="crit-header">
                <span class="crit-name">{k.replace("_", " ").title()}</span>
                <span class="crit-score">{sc}/10</span>
              </div>
              <div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{bar_color}"></div></div>
              <div class="crit-just">{just}</div>
            </div>"""

        strengths_html = "".join(f"<li>{s}</li>" for s in r.get("key_strengths", []))
        concerns_html = "".join(f"<li>{c}</li>" for c in r.get("key_concerns", []))

        cards_html += f"""
        <div class="pitch-card">
          <div class="card-header">
            <div class="rank-badge">#{r["rank"]}</div>
            <div class="pitch-meta">
              <h2 class="pitch-name">{r["pitch_name"]}</h2>
              <span class="source-tag">{sources}</span>
            </div>
            <div class="score-block">
              <div class="total-score">{score:.1f}<span>/10</span></div>
              <div class="rec-badge" style="background:{color}20;color:{color};border:1px solid {color}">{emoji} {rec}</div>
            </div>
          </div>

          <div class="card-body">
            <div class="summary-section">
              <h3>Overall Assessment</h3>
              <p>{r.get("overall_summary", "")}</p>
            </div>

            <div class="two-col">
              <div>
                <h3>Key Strengths</h3>
                <ul class="green-list">{strengths_html}</ul>
              </div>
              <div>
                <h3>Key Concerns</h3>
                <ul class="red-list">{concerns_html}</ul>
              </div>
            </div>

            <div class="criteria-section">
              <h3>Criteria Breakdown</h3>
              <div class="criteria-grid">{criteria_html}</div>
            </div>
          </div>
        </div>"""

    # Leaderboard rows
    leaderboard_rows = ""
    for r in ranked:
        rec = r.get("recommendation", "Unknown")
        color = RECOMMENDATION_COLORS.get(rec, "#94a3b8")
        emoji = RECOMMENDATION_EMOJI.get(rec, "⚪")
        leaderboard_rows += f"""
        <tr>
          <td class="rank-cell">#{r["rank"]}</td>
          <td class="name-cell">{r["pitch_name"]}</td>
          <td class="score-cell">{r.get("weighted_total", 0):.1f}</td>
          <td><span class="rec-pill" style="background:{color}20;color:{color};border:1px solid {color}">{emoji} {rec}</span></td>
        </tr>"""

    radar_labels = [k.replace("_", " ").title() for k in criteria_keys]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pitch Analysis Report — {timestamp}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg: #0a0e1a;
    --surface: #111827;
    --border: #1f2937;
    --text: #e2e8f0;
    --muted: #64748b;
    --accent: #6366f1;
  }}

  body {{
    font-family: 'IBM Plex Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 0 0 60px;
  }}

  header {{
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    border-bottom: 1px solid #312e81;
    padding: 40px 60px;
    position: relative;
    overflow: hidden;
  }}
  header::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 80% 50%, rgba(99,102,241,0.15) 0%, transparent 70%);
  }}
  header h1 {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    letter-spacing: -0.5px;
    color: #fff;
  }}
  header .sub {{
    color: #a5b4fc;
    margin-top: 6px;
    font-size: 0.9rem;
    font-family: 'IBM Plex Mono', monospace;
  }}

  .container {{ max-width: 1100px; margin: 0 auto; padding: 0 40px; }}

  /* Leaderboard */
  .leaderboard-section {{
    margin-top: 50px;
  }}
  .section-title {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 20px;
  }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
    padding: 10px 16px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }}
  td {{
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    font-size: 0.95rem;
  }}
  tr:hover td {{ background: rgba(99,102,241,0.05); }}
  .rank-cell {{ font-family: 'IBM Plex Mono', monospace; color: var(--muted); }}
  .name-cell {{ font-weight: 500; }}
  .score-cell {{ font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 1.1rem; color: #a5b4fc; }}
  .rec-pill {{
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 500;
    white-space: nowrap;
  }}

  /* Radar chart */
  .radar-section {{ margin-top: 50px; }}
  .radar-wrapper {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 30px;
    display: flex;
    justify-content: center;
  }}
  canvas {{ max-height: 420px; }}

  /* Pitch cards */
  .cards-section {{ margin-top: 50px; }}
  .pitch-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 28px;
    overflow: hidden;
    transition: border-color 0.2s;
  }}
  .pitch-card:hover {{ border-color: #374151; }}

  .card-header {{
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 24px 28px;
    border-bottom: 1px solid var(--border);
    background: rgba(255,255,255,0.02);
  }}
  .rank-badge {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--accent);
    min-width: 60px;
  }}
  .pitch-meta {{ flex: 1; }}
  .pitch-name {{ font-size: 1.3rem; font-weight: 600; }}
  .source-tag {{
    font-size: 0.75rem;
    color: var(--muted);
    font-family: 'IBM Plex Mono', monospace;
    margin-top: 4px;
    display: block;
  }}
  .score-block {{ text-align: right; }}
  .total-score {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.2rem;
    font-weight: 600;
    color: #fff;
    line-height: 1;
  }}
  .total-score span {{ font-size: 1rem; color: var(--muted); }}
  .rec-badge {{
    display: inline-block;
    margin-top: 8px;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 500;
    white-space: nowrap;
  }}

  .card-body {{ padding: 28px; }}

  .summary-section h3,
  .two-col h3,
  .criteria-section h3 {{
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
    font-family: 'IBM Plex Mono', monospace;
  }}
  .summary-section p {{ line-height: 1.7; color: #cbd5e1; }}

  .two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-top: 24px;
  }}
  .green-list, .red-list {{ list-style: none; padding: 0; }}
  .green-list li {{ padding: 5px 0; padding-left: 18px; position: relative; color: #86efac; font-size: 0.9rem; }}
  .green-list li::before {{ content: '+'; position: absolute; left: 0; color: #22c55e; font-weight: 700; }}
  .red-list li {{ padding: 5px 0; padding-left: 18px; position: relative; color: #fca5a5; font-size: 0.9rem; }}
  .red-list li::before {{ content: '–'; position: absolute; left: 0; color: #ef4444; font-weight: 700; }}

  .criteria-section {{ margin-top: 24px; }}
  .criteria-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 12px; }}
  .criterion {{ background: rgba(0,0,0,0.2); border-radius: 8px; padding: 14px; }}
  .crit-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
  .crit-name {{ font-size: 0.8rem; font-weight: 500; color: #94a3b8; text-transform: capitalize; }}
  .crit-score {{ font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.9rem; }}
  .bar-bg {{ height: 4px; background: #1f2937; border-radius: 2px; margin-bottom: 8px; }}
  .bar-fill {{ height: 100%; border-radius: 2px; transition: width 0.5s ease; }}
  .crit-just {{ font-size: 0.8rem; color: var(--muted); line-height: 1.5; }}

  @media (max-width: 700px) {{
    header {{ padding: 30px 20px; }}
    .container {{ padding: 0 16px; }}
    .criteria-grid, .two-col {{ grid-template-columns: 1fr; }}
    .card-header {{ flex-wrap: wrap; }}
  }}
</style>
</head>
<body>
<header>
  <div class="container">
    <h1>📊 Pitch Analysis Report</h1>
    <div class="sub">Generated {timestamp} · {len(ranked)} pitch(es) evaluated · Local AI analysis</div>
  </div>
</header>

<div class="container">

  <div class="leaderboard-section">
    <div class="section-title">Rankings</div>
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Pitch</th>
          <th>Score</th>
          <th>Recommendation</th>
        </tr>
      </thead>
      <tbody>{leaderboard_rows}</tbody>
    </table>
  </div>

  <div class="radar-section">
    <div class="section-title">Criteria Comparison</div>
    <div class="radar-wrapper">
      <canvas id="radarChart" width="600" height="420"></canvas>
    </div>
  </div>

  <div class="cards-section">
    <div class="section-title">Detailed Assessments</div>
    {cards_html}
  </div>

</div>

<script>
const ctx = document.getElementById('radarChart').getContext('2d');
new Chart(ctx, {{
  type: 'radar',
  data: {{
    labels: {json.dumps(radar_labels)},
    datasets: {json.dumps(radar_datasets)}
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{
        labels: {{ color: '#94a3b8', font: {{ family: 'IBM Plex Mono', size: 11 }} }}
      }}
    }},
    scales: {{
      r: {{
        min: 0, max: 10,
        ticks: {{ stepSize: 2, color: '#475569', backdropColor: 'transparent', font: {{ family: 'IBM Plex Mono', size: 10 }} }},
        grid: {{ color: '#1f2937' }},
        pointLabels: {{ color: '#94a3b8', font: {{ family: 'IBM Plex Sans', size: 11 }} }},
        angleLines: {{ color: '#1f2937' }}
      }}
    }}
  }}
}});
</script>
</body>
</html>"""

    path = os.path.join(output_dir, "report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  🌐 HTML report saved: {path}")


def _print_summary(ranked: list[dict]):
    print(f"\n  {'─' * 56}")
    print(f"  {'RANK':<6} {'PITCH NAME':<30} {'SCORE':<8} RECOMMENDATION")
    print(f"  {'─' * 56}")
    for r in ranked:
        emoji = RECOMMENDATION_EMOJI.get(r.get("recommendation", "Unknown"), "⚪")
        print(
            f"  #{r['rank']:<5} {r['pitch_name']:<30} "
            f"{r.get('weighted_total', 0):<8.1f} "
            f"{emoji} {r.get('recommendation', 'Unknown')}"
        )
    print(f"  {'─' * 56}")
