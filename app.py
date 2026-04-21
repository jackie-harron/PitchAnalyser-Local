"""
app.py - Streamlit web UI for PitchAnalyser Local
Run with: streamlit run app.py
"""

import streamlit as st
import os
import json
import tempfile
import shutil
import shutil as sh  # aliased for ffmpeg check below
import time
from pathlib import Path

# Page config — must be first Streamlit call
st.set_page_config(
    page_title="PitchAnalyser Local",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Hide default Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

/* App header */
.app-header {
    background: linear-gradient(135deg, #0f0c29, #1a1a2e, #16213e);
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    border: 1px solid rgba(255,255,255,0.06);
    position: relative;
    overflow: hidden;
}
.app-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.app-header h1 {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: white;
    margin: 0;
    letter-spacing: -1px;
}
.app-header p {
    color: rgba(255,255,255,0.5);
    margin: 0.5rem 0 0;
    font-size: 1rem;
}
.privacy-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(34,197,94,0.1);
    border: 1px solid rgba(34,197,94,0.3);
    color: #86efac;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    margin-top: 1rem;
}

/* Status cards */
.status-card {
    background: #1e293b;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    border-left: 4px solid #475569;
    margin-bottom: 0.75rem;
}
.status-card.ok   { border-left-color: #22c55e; }
.status-card.warn { border-left-color: #f59e0b; }
.status-card.err  { border-left-color: #ef4444; }
.status-title { font-weight: 600; font-size: 0.95rem; margin-bottom: 0.2rem; color: #f1f5f9; }
.status-desc  { font-size: 0.82rem; color: #94a3b8; }

/* Rubric editor */
.rubric-row {
    background: #1e293b;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    border: 1px solid #334155;
}

/* Result cards */
.result-card {
    background: linear-gradient(145deg, #1e293b, #162032);
    border-radius: 14px;
    padding: 1.8rem;
    border: 1px solid #334155;
    margin-bottom: 1.2rem;
    transition: border-color 0.2s;
}
.result-card:hover { border-color: #475569; }
.result-rank {
    font-family: 'Syne', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    color: #6366f1;
    line-height: 1;
}
.result-name {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #f1f5f9;
}
.result-score {
    font-family: 'Syne', sans-serif;
    font-size: 2.5rem;
    font-weight: 800;
    color: white;
}
.score-bar-bg {
    background: #334155;
    border-radius: 4px;
    height: 6px;
    margin: 4px 0 8px;
}
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 500;
}

/* ── Section headers ── */
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-color, inherit) !important;
    margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e293b;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.6rem 2rem !important;
    font-size: 1rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Imports (after page config) ─────────────────────────────────────────────
from pitchanalyser.scorer import check_ollama_running, check_model_available
from pitchanalyser.extractor import extract_frames_from_video, extract_pages_from_deck
from pitchanalyser.scorer import score_pitch
from pitchanalyser.reporter import rank_results, _write_html, _write_json


# ── Session state defaults ───────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = []
if "rubric" not in st.session_state:
    st.session_state.rubric = {
        "problem_clarity": {
            "description": "How clearly is the problem defined? Is it compelling?",
            "weight": 1.0,
        },
        "solution_viability": {
            "description": "Is the solution practical and well-explained?",
            "weight": 1.0,
        },
        "market_opportunity": {
            "description": "Is the target market clearly defined and significant?",
            "weight": 1.0,
        },
        "business_model": {
            "description": "Is there a clear path to revenue and profitability?",
            "weight": 1.0,
        },
        "traction_evidence": {
            "description": "Is there evidence of customer validation or traction?",
            "weight": 1.0,
        },
        "team_credibility": {
            "description": "Does the team have the experience to execute?",
            "weight": 1.0,
        },
        "competitive_advantage": {
            "description": "Is there a defensible moat or unfair advantage?",
            "weight": 1.0,
        },
        "presentation_quality": {
            "description": "Is the pitch clear, structured, and well-delivered?",
            "weight": 0.75,
        },
    }


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="app-header">
    <h1>🎯 PitchAnalyser Local</h1>
    <p>Upload pitch videos and decks · Score against your rubric · Get ranked results</p>
    <div class="privacy-badge">🔒 100% Local — no data leaves this machine</div>
</div>
""",
    unsafe_allow_html=True,
)


# ── Sidebar: System Status & Settings ────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    model = st.selectbox(
        "Vision Model",
        ["qwen2.5vl", "qwen2.5vl:72b", "llava:7b", "llama3.2-vision", "llava:13b"],
        help="Model must be pulled in Ollama first",
    )

    frames_per_min = st.slider(
        "Video frames per minute",
        min_value=1,
        max_value=6,
        value=2,
        help="More frames = better analysis but slower",
    )

    st.markdown("---")
    st.markdown("### 🔌 System Status")

    # Ollama check
    ollama_ok = check_ollama_running()
    if ollama_ok:
        st.markdown(
            '<div class="status-card ok"><div class="status-title">✅ Ollama Running</div><div class="status-desc">Local AI server is active</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-card err"><div class="status-title">❌ Ollama Not Running</div><div class="status-desc">Start Ollama app or run: ollama serve</div></div>',
            unsafe_allow_html=True,
        )

    # Model check
    if ollama_ok:
        model_ok = check_model_available(model)
        if model_ok:
            st.markdown(
                f'<div class="status-card ok"><div class="status-title">✅ Model Ready</div><div class="status-desc">{model} is available</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="status-card warn"><div class="status-title">⚠️ Model Not Pulled</div><div class="status-desc">Run: ollama pull {model}</div></div>',
                unsafe_allow_html=True,
            )

    # ffmpeg check
    ffmpeg_ok = sh.which("ffmpeg") is not None
    if ffmpeg_ok:
        st.markdown(
            '<div class="status-card ok"><div class="status-title">✅ ffmpeg Found</div><div class="status-desc">Video analysis supported</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-card warn"><div class="status-title">⚠️ ffmpeg Missing</div><div class="status-desc">Videos cannot be processed</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### 📥 Load Custom Rubric")
    rubric_file = st.file_uploader(
        "Upload rubric JSON", type=["json"], label_visibility="collapsed"
    )
    if rubric_file:
        try:
            loaded = json.load(rubric_file)
            # Strip _comment/_note keys
            loaded = {k: v for k, v in loaded.items() if not k.startswith("_")}
            st.session_state.rubric = loaded
            st.success(f"Loaded {len(loaded)} criteria")
        except Exception as e:
            st.error(f"Invalid JSON: {e}")


# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📤  Upload & Analyse", "📋  Rubric Editor", "📊  Results"])


# ── TAB 1: Upload & Analyse ───────────────────────────────────────────────────
with tab1:
    st.markdown(
        '<div class="section-header">Upload Pitch Files</div>', unsafe_allow_html=True
    )
    st.caption(
        "Upload one or more pitches. If a video and deck share the same filename (e.g. `AcmeCorp.mp4` + `AcmeCorp.pdf`), they'll be analysed together."
    )

    uploaded_files = st.file_uploader(
        "Drop pitch files here",
        type=["mp4", "mov", "avi", "mkv", "webm", "pdf", "pptx", "ppt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        # Group by stem
        grouped = {}
        for f in uploaded_files:
            stem = Path(f.name).stem
            ext = Path(f.name).suffix.lower()
            if stem not in grouped:
                grouped[stem] = {
                    "name": stem,
                    "video": None,
                    "deck": None,
                    "video_name": None,
                    "deck_name": None,
                }
            if ext in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
                grouped[stem]["video"] = f
                grouped[stem]["video_name"] = f.name
            elif ext in {".pdf", ".pptx", ".ppt"}:
                grouped[stem]["deck"] = f
                grouped[stem]["deck_name"] = f.name

        st.markdown(f"**{len(grouped)} pitch(es) detected:**")
        for name, p in grouped.items():
            v = f"🎬 {p['video_name']}" if p["video"] else "_(no video)_"
            d = f"📑 {p['deck_name']}" if p["deck"] else "_(no deck)_"
            st.markdown(f"- **{name}** — {v} · {d}")

        st.markdown("---")

        if not ollama_ok:
            st.error("⛔ Ollama is not running. Please start it before analysing.")
        elif not check_model_available(model):
            st.warning(
                f"⚠️ Model `{model}` is not pulled yet. Run: `ollama pull {model}`"
            )

        run_btn = st.button(
            "🚀  Analyse All Pitches",
            disabled=not (ollama_ok and check_model_available(model)),
            use_container_width=True,
        )

        if run_btn:
            results = []
            work_dir = tempfile.mkdtemp(prefix="pitch_analyser_")

            progress_bar = st.progress(0)
            status_text = st.empty()
            log_box = st.empty()
            log_lines = []

            def log(msg):
                log_lines.append(msg)
                log_box.code("\n".join(log_lines[-12:]), language=None)

            total = len(grouped)
            for i, (name, p) in enumerate(grouped.items()):
                status_text.markdown(f"**Analysing {i + 1}/{total}: {name}**")
                log(f"[{i + 1}/{total}] Starting: {name}")

                images = []
                sources = []
                pitch_dir = os.path.join(work_dir, name)
                os.makedirs(pitch_dir, exist_ok=True)

                # Save uploaded files to temp dir
                if p["video"]:
                    vid_path = os.path.join(pitch_dir, p["video_name"])
                    with open(vid_path, "wb") as f:
                        f.write(p["video"].read())
                    log("  → Extracting video frames...")
                    try:
                        frames = extract_frames_from_video(
                            vid_path,
                            output_dir=os.path.join(pitch_dir, "frames"),
                            frames_per_minute=frames_per_min,
                        )
                        images.extend(frames)
                        sources.append(f"Video ({len(frames)} frames)")
                        log(f"  → {len(frames)} frames extracted")
                    except Exception as e:
                        log(f"  ⚠ Video extraction failed: {e}")

                if p["deck"]:
                    deck_path = os.path.join(pitch_dir, p["deck_name"])
                    with open(deck_path, "wb") as f:
                        f.write(p["deck"].read())
                    log("  → Extracting deck pages...")
                    try:
                        pages = extract_pages_from_deck(
                            deck_path, output_dir=os.path.join(pitch_dir, "pages")
                        )
                        images.extend(pages)
                        sources.append(f"Deck ({len(pages)} pages)")
                        log(f"  → {len(pages)} pages extracted")
                    except Exception as e:
                        log(f"  ⚠ Deck extraction failed: {e}")

                if not images:
                    log(f"  ✗ No images extracted for {name}, skipping.")
                    continue

                log(f"  → Scoring with {model} ({len(images)} images)...")
                try:
                    t0 = time.time()
                    result = score_pitch(
                        pitch_name=name,
                        images=images,
                        rubric=st.session_state.rubric,
                        model=model,
                    )
                    result["sources"] = sources
                    results.append(result)
                    elapsed = time.time() - t0
                    log(
                        f"  ✓ Scored in {elapsed:.0f}s — {result.get('weighted_total', 0):.1f}/10"
                    )
                except Exception as e:
                    log(f"  ✗ Scoring failed: {e}")

                progress_bar.progress((i + 1) / total)

            # Save results
            st.session_state.results = rank_results(results)
            st.session_state.work_dir = work_dir

            # Generate downloadable report
            report_dir = os.path.join(work_dir, "report")
            os.makedirs(report_dir, exist_ok=True)
            for i, r in enumerate(st.session_state.results):
                r["rank"] = i + 1
            _write_html(st.session_state.results, st.session_state.rubric, report_dir)
            _write_json(st.session_state.results, st.session_state.rubric, report_dir)
            st.session_state.report_dir = report_dir

            status_text.markdown("✅ **Analysis complete!**")
            log("─── Done ───")

            st.success(
                f"✅ {len(results)} pitch(es) analysed! Switch to the **Results** tab to view rankings."
            )
            st.balloons()

            # Cleanup temp files (keep report)
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except:
                pass


# ── TAB 2: Rubric Editor ──────────────────────────────────────────────────────
with tab2:
    st.markdown(
        '<div class="section-header">Rubric Editor</div>', unsafe_allow_html=True
    )
    st.caption(
        "Customise the scoring criteria for your competition. Add, remove, or adjust weights."
    )

    rubric = st.session_state.rubric
    updated_rubric = {}

    col_add1, col_add2, col_add3 = st.columns([2, 2, 1])
    with col_add1:
        new_key = st.text_input(
            "New criterion key (no spaces)",
            placeholder="e.g. sustainability",
            label_visibility="collapsed",
        )
    with col_add2:
        new_desc = st.text_input(
            "Description",
            placeholder="What does this criterion measure?",
            label_visibility="collapsed",
        )
    with col_add3:
        if st.button("➕ Add", use_container_width=True):
            if new_key and new_desc:
                clean_key = new_key.strip().lower().replace(" ", "_")
                rubric[clean_key] = {"description": new_desc, "weight": 1.0}
                st.session_state.rubric = rubric
                st.rerun()

    st.markdown("---")

    keys_to_delete = []
    for key, val in rubric.items():
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 4, 1.5, 0.8])
            with c1:
                st.markdown(f"**{key.replace('_', ' ').title()}**")
            with c2:
                new_d = st.text_input(
                    "desc",
                    value=val["description"],
                    key=f"desc_{key}",
                    label_visibility="collapsed",
                )
            with c3:
                new_w = st.number_input(
                    "weight",
                    value=float(val["weight"]),
                    min_value=0.1,
                    max_value=5.0,
                    step=0.25,
                    key=f"w_{key}",
                    label_visibility="collapsed",
                )
            with c4:
                if st.button("🗑", key=f"del_{key}"):
                    keys_to_delete.append(key)
            updated_rubric[key] = {"description": new_d, "weight": new_w}

    for k in keys_to_delete:
        del updated_rubric[k]

    st.session_state.rubric = updated_rubric

    st.markdown("---")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        rubric_json = json.dumps(st.session_state.rubric, indent=2)
        st.download_button(
            "💾 Download Rubric as JSON",
            data=rubric_json,
            file_name="my_rubric.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_dl2:
        st.caption(
            f"**{len(st.session_state.rubric)} criteria** · Total weight: {sum(v['weight'] for v in st.session_state.rubric.values()):.2f}"
        )


# ── TAB 3: Results ────────────────────────────────────────────────────────────
with tab3:
    if not st.session_state.results:
        st.info(
            "No results yet. Upload and analyse some pitches in the **Upload & Analyse** tab."
        )
    else:
        results = st.session_state.results
        rubric = st.session_state.rubric

        # Summary leaderboard
        st.markdown(
            '<div class="section-header">🏆 Rankings</div>', unsafe_allow_html=True
        )

        REC_COLORS = {
            "Strong Pass": "#22c55e",
            "Pass": "#84cc16",
            "Borderline": "#f59e0b",
            "Pass with Concerns": "#f97316",
            "No Pass": "#ef4444",
            "Unknown": "#94a3b8",
        }

        # Leaderboard table
        header_cols = st.columns([0.5, 3, 1.5, 2, 1])
        header_cols[0].markdown("**#**")
        header_cols[1].markdown("**Pitch**")
        header_cols[2].markdown("**Score**")
        header_cols[3].markdown("**Recommendation**")
        header_cols[4].markdown("**Sources**")
        st.markdown("---")

        for i, r in enumerate(results):
            r["rank"] = i + 1
        for r in results:
            rec = r.get("recommendation", "Unknown")
            color = REC_COLORS.get(rec, "#94a3b8")
            cols = st.columns([0.5, 3, 1.5, 2, 1])
            cols[0].markdown(f"**#{r['rank']}**")
            cols[1].markdown(f"**{r['pitch_name']}**")
            cols[2].markdown(f"**{r.get('weighted_total', 0):.1f} / 10**")
            cols[3].markdown(
                f'<span style="color:{color};font-weight:600">{rec}</span>',
                unsafe_allow_html=True,
            )
            cols[4].markdown(", ".join(r.get("sources", [])))

        # Download buttons
        st.markdown("---")
        report_dir = st.session_state.get("report_dir")

        if report_dir:
            dl1, dl2, _ = st.columns([1.5, 1.5, 3])
            html_path = os.path.join(report_dir, "report.html")
            json_path = os.path.join(report_dir, "results.json")

            if os.path.exists(html_path):
                with open(html_path, "rb") as f:
                    dl1.download_button(
                        "📄 Download HTML Report",
                        f,
                        "pitch_report.html",
                        "text/html",
                        use_container_width=True,
                    )
            if os.path.exists(json_path):
                with open(json_path, "rb") as f:
                    dl2.download_button(
                        "📦 Download JSON Data",
                        f,
                        "pitch_results.json",
                        "application/json",
                        use_container_width=True,
                    )

        # Detailed pitch cards
        st.markdown(
            '<div class="section-header">Detailed Assessments</div>',
            unsafe_allow_html=True,
        )

        for r in results:
            rec = r.get("recommendation", "Unknown")
            color = REC_COLORS.get(rec, "#94a3b8")

            with st.expander(
                f"#{r['rank']} · {r['pitch_name']}  —  {r.get('weighted_total', 0):.1f}/10  ·  {rec}",
                expanded=(r["rank"] == 1),
            ):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown("**Overall Assessment**")
                    st.markdown(r.get("overall_summary", ""))
                with c2:
                    st.metric("Score", f"{r.get('weighted_total', 0):.1f} / 10")
                    st.markdown(
                        f'<span style="color:{color};font-weight:600;font-size:0.9rem">{rec}</span>',
                        unsafe_allow_html=True,
                    )

                col_s, col_c = st.columns(2)
                with col_s:
                    st.markdown("**✅ Key Strengths**")
                    for s in r.get("key_strengths", []):
                        st.markdown(f"- {s}")
                with col_c:
                    st.markdown("**⚠️ Key Concerns**")
                    for c in r.get("key_concerns", []):
                        st.markdown(f"- {c}")

                st.markdown("**Criteria Scores**")
                scores = r.get("scores", {})
                crit_keys = list(rubric.keys())

                for i in range(0, len(crit_keys), 2):
                    cols = st.columns(2)
                    for j, col in enumerate(cols):
                        if i + j < len(crit_keys):
                            k = crit_keys[i + j]
                            s = scores.get(k, {})
                            sc = s.get("score", 0)
                            just = s.get("justification", "")
                            bar_color = (
                                "#22c55e"
                                if sc >= 7
                                else "#f59e0b"
                                if sc >= 4
                                else "#ef4444"
                            )
                            with col:
                                st.markdown(
                                    f'<div style="background:#1e293b;border-radius:10px;padding:12px 14px;margin-bottom:10px">'
                                    f'<div style="display:flex;justify-content:space-between;margin-bottom:6px">'
                                    f'<span style="font-weight:600;font-size:0.85rem;color:#94a3b8">{k.replace("_", " ").title()}</span>'
                                    f'<span style="font-weight:700;color:{bar_color}">{sc}/10</span></div>'
                                    f'<div style="background:#334155;border-radius:3px;height:5px;margin-bottom:8px">'
                                    f'<div style="width:{sc * 10}%;background:{bar_color};height:100%;border-radius:3px"></div></div>'
                                    f'<div style="font-size:0.8rem;color:#64748b;line-height:1.5">{just}</div>'
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )
