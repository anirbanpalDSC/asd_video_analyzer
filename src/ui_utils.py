"""Shared Streamlit UI components for the ASD Video Analyzer app."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import streamlit as st

from config.config import DEFAULT_ASD_PROMPT

# Ordered signal names — must match the numbering in DEFAULT_ASD_PROMPT
SIGNAL_NAMES: List[str] = [
    "Absence or Avoidance of Eye Contact",
    "Aggressive Behavior",
    "Hyper- or Hyporeactivity to Sensory Input",
    "Non-Responsiveness to Verbal Interaction",
    "Non-Typical Language",
    "Object Lining-Up",
    "Self-Hitting or Self-Injurious Behavior",
    "Self-Spinning or Spinning Objects",
    "Upper Limb Stereotypies",
    "Background",
]

# Confidence thresholds (fraction of frames)
_HIGH_THRESHOLD = 0.70   # >= 70% -> High
_MEDIUM_THRESHOLD = 0.30 # >= 30% -> Medium, else -> Low


def get_default_asd_prompt() -> str:
    """Return the default ASD behavioral analysis prompt."""
    return DEFAULT_ASD_PROMPT


# ---------------------------------------------------------------------------
# Frame-detection helpers
# ---------------------------------------------------------------------------

def _parse_frame_detections(section_text: str) -> Dict[int, List]:
    """Parse the FRAME_DETECTIONS section into per-signal presence lists.

    Expected line format (one per frame):
        Frame_1: 1=Yes,2=No,3=Yes,...,10=No

    Returns a dict {signal_index (1-based): [True/False/None, ...per frame]}.
    """
    detections: Dict[int, List] = {i + 1: [] for i in range(len(SIGNAL_NAMES))}
    for line in section_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if not line.lower().startswith("frame"):
            continue
        colon_pos = line.find(":")
        if colon_pos < 0:
            continue
        pairs_str = line[colon_pos + 1:].strip()
        for pair in pairs_str.split(","):
            pair = pair.strip()
            if "=" not in pair:
                continue
            idx_str, val_str = pair.split("=", 1)
            try:
                idx = int(idx_str.strip())
                v = val_str.strip().lower()
                if v in ("yes", "true", "1"):
                    present: bool | None = True
                elif v in ("unclear", "unknown", "n/a"):
                    present = None
                else:
                    present = False
                if 1 <= idx <= len(SIGNAL_NAMES):
                    detections[idx].append(present)
            except ValueError:
                continue
    return detections


def _compute_confidence(detection_list: List, observed: str = "Yes") -> Tuple[str, int, int]:
    """Return (confidence_label, detected_count, assessable_frames).

    Confidence reflects certainty in the *observed outcome*, not raw detection rate:
    - Observed=Yes  → scales with detection rate   (more detections → Higher confidence)
    - Observed=No   → scales with absence rate      (fewer detections → Higher confidence)

    None values (Unclear) are excluded from both numerator and denominator.
    """
    assessable = [v for v in detection_list if v is not None]
    total = len(assessable)
    if total == 0:
        return "N/A", 0, 0
    count = sum(1 for v in assessable if v)
    detection_pct = count / total

    if observed.lower() == "yes":
        pct = detection_pct          # high detections → confident Yes
    else:
        pct = 1.0 - detection_pct   # high absences → confident No

    if pct >= _HIGH_THRESHOLD:
        label = "High"
    elif pct >= _MEDIUM_THRESHOLD:
        label = "Medium"
    else:
        label = "Low"
    return label, count, total


def _badge(label: str, kind: str, dark: bool) -> str:
    """Return an inline-styled HTML badge.

    kind: 'yes' | 'no' | 'neutral' | 'high' | 'medium' | 'low'
    """
    if dark:
        styles = {
            "yes":     "background:rgba(74,222,128,0.18);color:#4ade80;border:1.5px solid #4ade80",
            "no":      "background:rgba(248,113,113,0.18);color:#f87171;border:1.5px solid #f87171",
            "neutral": "background:rgba(148,163,184,0.18);color:#94a3b8;border:1.5px solid #94a3b8",
            "high":    "background:rgba(74,222,128,0.18);color:#4ade80;border:1.5px solid #4ade80",
            "medium":  "background:rgba(250,204,21,0.18);color:#facc15;border:1.5px solid #facc15",
            "low":     "background:rgba(248,113,113,0.18);color:#f87171;border:1.5px solid #f87171",
        }
    else:
        styles = {
            "yes":     "background:#d4edda;color:#155724",
            "no":      "background:#f8d7da;color:#721c24",
            "neutral": "background:#e2e8f0;color:#4a5568",
            "high":    "background:#d4edda;color:#155724",
            "medium":  "background:#fff3cd;color:#856404",
            "low":     "background:#f8d7da;color:#721c24",
        }
    style = styles.get(kind, styles["neutral"])
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:12px;'
        f'font-size:0.82em;font-weight:700;{style}">{label}</span>'
    )


def _confidence_badge(val: str, dark: bool = False) -> str:
    kind = val.lower() if val.lower() in ("high", "medium", "low") else "neutral"
    return _badge(val, kind, dark)


def _normalize_observed(val: str) -> str:
    """Collapse multi-value LLM outputs like 'Yes/No/Unclear' to a single word.

    Priority: Yes > Unclear > No.  Matches against all slash- or comma-separated
    tokens so 'No/No/No' → 'No' and 'Yes/No/Unclear' → 'Yes'.
    """
    tokens = [t.strip().lower() for t in val.replace(",", "/").split("/")]
    if any(t in ("yes", "true", "1") for t in tokens):
        return "Yes"
    if any(t in ("unclear", "unknown", "n/a") for t in tokens):
        return "Unclear"
    return "No"


def _observed_badge(val: str, dark: bool = False) -> str:
    normalized = _normalize_observed(val)
    kind = "yes" if normalized == "Yes" else ("no" if normalized == "No" else "neutral")
    return _badge(normalized, kind, dark)


# ---------------------------------------------------------------------------
# Main display function
# ---------------------------------------------------------------------------

def parse_and_display_analysis(analysis_text: str) -> None:
    """Parse LLM analysis output and display signals table + narrative.

    Supports the new format (FRAME_DETECTIONS + SIGNALS with 3 cols) as well
    as the legacy 4-column format (Signal | Observed | Confidence | Note).
    When FRAME_DETECTIONS is present, confidence is computed from frame
    frequency rather than taken from the LLM output.
    """
    if "SIGNALS:" not in analysis_text:
        st.markdown(analysis_text)
        return

    # ── Split into sections ──────────────────────────────────────────────────
    frame_detections: Dict[int, List[bool]] = {}
    n_frames_parsed = 0

    if "FRAME_DETECTIONS:" in analysis_text:
        fd_start = analysis_text.index("FRAME_DETECTIONS:") + len("FRAME_DETECTIONS:")
        fd_end = analysis_text.index("SIGNALS:")
        fd_text = analysis_text[fd_start:fd_end]
        frame_detections = _parse_frame_detections(fd_text)
        n_frames_parsed = len(frame_detections.get(1, []))

    sig_start = analysis_text.index("SIGNALS:") + len("SIGNALS:")
    if "CLINICAL NARRATIVE:" in analysis_text:
        sig_end = analysis_text.index("CLINICAL NARRATIVE:")
        narrative_text = analysis_text[analysis_text.index("CLINICAL NARRATIVE:") + len("CLINICAL NARRATIVE:"):].strip()
    else:
        sig_end = len(analysis_text)
        narrative_text = ""

    signals_section = analysis_text[sig_start:sig_end]

    # ── Parse SIGNALS rows ───────────────────────────────────────────────────
    rows = []
    leftover_lines = []
    for line in signals_section.split("\n"):
        line = line.strip()
        if not line or line.startswith("---"):
            continue
        if "|" in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 3:
                # New format: Signal | Observed | Note (3 cols)
                # Legacy format: Signal | Observed | Confidence | Note (4 cols)
                rows.append({
                    "Signal": cells[0],
                    "Observed": cells[1],
                    "_llm_confidence": cells[2] if len(cells) == 4 else "",
                    "Note": cells[3] if len(cells) >= 4 else cells[2],
                })
            elif len(cells) > 0:
                leftover_lines.extend(cells)
        else:
            leftover_lines.append(line)

    if not rows:
        st.markdown(analysis_text)
        return

    # ── Merge frequency-based confidence ────────────────────────────────────
    use_frequency = bool(frame_detections and n_frames_parsed > 0)

    display_rows = []
    for row in rows:
        signal_name = row["Signal"]
        try:
            sig_idx = next(
                i + 1
                for i, name in enumerate(SIGNAL_NAMES)
                if name.lower() in signal_name.lower() or signal_name.lower() in name.lower()
            )
        except StopIteration:
            sig_idx = None

        observed_val = _normalize_observed(row["Observed"])

        if use_frequency and sig_idx is not None:
            det_list = frame_detections.get(sig_idx, [])
            conf_label, detected, total = _compute_confidence(det_list, observed_val)
            if total > 0:
                absent = total - detected
                if observed_val == "Yes":
                    frames_col = f"{detected}/{total} frames showed signal ({int(detected/total*100)}%)"
                else:
                    frames_col = f"{absent}/{total} frames showed no signal ({int(absent/total*100)}%)"
            else:
                frames_col = "N/A"
        else:
            conf_label = row["_llm_confidence"] or "N/A"
            frames_col = "N/A"

        display_rows.append({
            "Signal": row["Signal"],
            "Observed": observed_val,
            "Confidence": conf_label,
            "Frame Evidence": frames_col,
            "Note": row["Note"],
        })

    # ── Explainability note ──────────────────────────────────────────────────
    if use_frequency:
        st.info(
            f"**Confidence** reflects certainty in the *observed outcome* across "
            f"all {n_frames_parsed} frame(s) — not a raw detection rate. "
            f"For a **Yes** signal, High means the behaviour was seen in most frames. "
            f"For a **No** signal, High means the behaviour was consistently *absent* "
            f"(e.g. 0/10 frames with signal = High confidence of No). "
            f"**High** \u2265 70% | **Medium** 30\u201369% | **Low** < 30%."
        )
    else:
        st.caption(
            "Note: Confidence ratings reflect the model's qualitative judgment. "
            "For frequency-based confidence, ensure the default analysis prompt is used."
        )

    # ── HTML table (theme-safe — avoids AG Grid dark-mode issues) ────────────
    dark = st.session_state.get("theme", "light") == "dark"

    col_names = ["Signal", "Observed", "Confidence", "Frame Evidence", "Note"]

    if dark:
        th_style = (
            "background:#1e2130;color:#c8d0e8;font-weight:600;font-size:0.85em;"
            "padding:8px 12px;text-align:left;border-bottom:2px solid #2e3450;"
        )
        td_style = (
            "padding:8px 12px;font-size:0.88em;color:#c8d0e8;"
            "border-bottom:1px solid #232840;vertical-align:top;"
        )
        tr_even = "background:#161922;"
        tr_odd  = "background:#1c2030;"
        wrap_style = "border:1px solid #2e3450;"
    else:
        th_style = (
            "background:#f0f4ff;color:#17191f;font-weight:600;font-size:0.85em;"
            "padding:8px 12px;text-align:left;border-bottom:2px solid #d0d7e8;"
        )
        td_style = (
            "padding:8px 12px;font-size:0.88em;color:#17191f;"
            "border-bottom:1px solid #e8ecf4;vertical-align:top;"
        )
        tr_even = "background:#ffffff;"
        tr_odd  = "background:#f8faff;"
        wrap_style = "border:1px solid #d0d7e8;"

    body_rows = []
    for i, row in enumerate(display_rows):
        bg = tr_even if i % 2 == 0 else tr_odd
        cells = [
            f'<td style="{td_style}">{row["Signal"]}</td>',
            f'<td style="{td_style}">{_observed_badge(row["Observed"], dark)}</td>',
            f'<td style="{td_style}">{_confidence_badge(row["Confidence"], dark)}</td>',
            f'<td style="{td_style}">{row["Frame Evidence"]}</td>',
            f'<td style="{td_style}">{row["Note"]}</td>',
        ]
        body_rows.append(f'<tr style="{bg}">{"".join(cells)}</tr>')

    header_html = "".join(f"<th style='{th_style}'>{c}</th>" for c in col_names)
    body_html = "".join(body_rows)
    table_html = (
        f'<div style="overflow-x:auto;border-radius:12px;{wrap_style}margin-bottom:1rem;">'
        '<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr>{header_html}</tr></thead>'
        f'<tbody>{body_html}</tbody>'
        '</table></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)

    # ── CSV download ─────────────────────────────────────────────────────────
    import io, csv
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=col_names)
    writer.writeheader()
    for row in display_rows:
        writer.writerow({c: row[c] for c in col_names})
    st.download_button(
        label="⬇️ Download CSV",
        data=buf.getvalue(),
        file_name="asd_analysis.csv",
        mime="text/csv",
    )

    # ── Clinical narrative ───────────────────────────────────────────────────
    extra = "\n".join(leftover_lines).strip()
    full_narrative = "\n".join(filter(None, [narrative_text, extra])).strip()
    if full_narrative:
        st.markdown("### Clinical Observations")
        st.write(full_narrative)


def show_upload_status(saved_name: str) -> None:
    st.success(f"Upload successful! Saved as `{saved_name}`")


def video_selector(videos: List[str]) -> str:
    """Return the video filename selected by the user or empty string."""
    if not videos:
        st.info("No videos uploaded yet.")
        return ""
    return st.selectbox("Choose a video", videos)


def show_video_info(
    video_filename: str,
    thumbs: List[Path],
    transcript: str | None,
    mp3: Path | None,
) -> List[Path]:
    """Render the detail view for a single video.

    Returns the list of thumbnails the user has ticked for analysis.
    """
    st.header(video_filename)
    if mp3:
        st.audio(str(mp3))
    if transcript:
        with st.expander("Transcript"):
            st.text_area("", transcript, height=200)
    if thumbs:
        st.write("Select thumbnails to include:")
        cols = st.columns(4)
        selected = []
        for idx, thumb in enumerate(thumbs):
            with cols[idx % 4]:
                st.image(str(thumb), width="stretch")
                chosen = st.checkbox(f"{thumb.name}", key=str(thumb))
                if chosen:
                    selected.append(thumb)
        return selected
    else:
        st.info("No thumbnails available for this video yet.")
        return []
