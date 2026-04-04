"""Shared Streamlit UI components for the ASD Video Analyzer app."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

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
_HIGH_THRESHOLD = 0.70   # ≥ 70 % → High
_MEDIUM_THRESHOLD = 0.30 # ≥ 30 % → Medium, else → Low


def get_default_asd_prompt() -> str:
    """Return the default ASD behavioral analysis prompt."""
    return DEFAULT_ASD_PROMPT


# ---------------------------------------------------------------------------
# Frame-detection helpers
# ---------------------------------------------------------------------------

def _parse_frame_detections(section_text: str) -> Dict[int, List[bool]]:
    """Parse the FRAME_DETECTIONS section into per-signal presence lists.

    Expected line format (one per frame):
        Frame_1: 1=Yes,2=No,3=Yes,...,10=No

    Returns a dict {signal_index (1-based): [True/False, ...per frame]}.
    """
    detections: Dict[int, List[bool]] = {i + 1: [] for i in range(len(SIGNAL_NAMES))}
    for line in section_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Accept "Frame_N:" or "Frame N:" prefixes
        lower = line.lower()
        if not lower.startswith("frame"):
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
                present = val_str.strip().lower() in ("yes", "true", "1")
                if 1 <= idx <= len(SIGNAL_NAMES):
                    detections[idx].append(present)
            except ValueError:
                continue
    return detections


def _compute_confidence(detection_list: List[bool]) -> Tuple[str, int, int]:
    """Return (confidence_label, detected_count, total_frames)."""
    total = len(detection_list)
    if total == 0:
        return "N/A", 0, 0
    count = sum(detection_list)
    pct = count / total
    if pct >= _HIGH_THRESHOLD:
        label = "High"
    elif pct >= _MEDIUM_THRESHOLD:
        label = "Medium"
    else:
        label = "Low"
    return label, count, total


def _confidence_color(val: str) -> str:
    """Return CSS style string for confidence badge coloring."""
    colors = {
        "High":   "background-color:#d4edda;color:#155724;font-weight:600",
        "Medium": "background-color:#fff3cd;color:#856404;font-weight:600",
        "Low":    "background-color:#f8d7da;color:#721c24;font-weight:600",
    }
    return colors.get(val, "")


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
        # Count how many frames were actually parsed (use signal 1 as proxy)
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
                # New format: Signal | Observed | Note (confidence computed below)
                # Legacy format: Signal | Observed | Confidence | Note
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

    # ── Merge frequency-based confidence ─────────────────────────────────────
    use_frequency = bool(frame_detections and n_frames_parsed > 0)

    display_rows = []
    for row_idx, row in enumerate(rows):
        signal_name = row["Signal"]
        # Match signal name to 1-based index in SIGNAL_NAMES
        try:
            sig_idx = next(
                i + 1
                for i, name in enumerate(SIGNAL_NAMES)
                if name.lower() in signal_name.lower() or signal_name.lower() in name.lower()
            )
        except StopIteration:
            sig_idx = None

        if use_frequency and sig_idx is not None:
            det_list = frame_detections.get(sig_idx, [])
            conf_label, detected, total = _compute_confidence(det_list)
            frames_col = f"{detected} / {total} ({int(detected/total*100) if total else 0}%)"
        else:
            conf_label = row["_llm_confidence"] or "N/A"
            frames_col = "N/A"

        display_rows.append({
            "Signal": row["Signal"],
            "Observed": row["Observed"],
            "Confidence": conf_label,
            "Frames Detected": frames_col,
            "Note": row["Note"],
        })

    df = pd.DataFrame(display_rows)

    # ── Explainability note ───────────────────────────────────────────────────
    if use_frequency:
        st.info(
            f"**Confidence methodology:** Each signal was evaluated independently "
            f"across all {n_frames_parsed} frame(s). "
            f"Confidence reflects the proportion of frames in which the signal was detected — "
            f"**High** ≥ 70 % | **Medium** 30–69 % | **Low** < 30 %."
        )
    else:
        st.caption(
            "Note: Confidence ratings reflect the model's qualitative judgment. "
            "For frequency-based confidence, ensure the default analysis prompt is used."
        )

    # ── Styled table ──────────────────────────────────────────────────────────
    styled = df.style.map(_confidence_color, subset=["Confidence"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Clinical narrative ────────────────────────────────────────────────────
    # Collect any leftover lines that weren't in the narrative section
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
