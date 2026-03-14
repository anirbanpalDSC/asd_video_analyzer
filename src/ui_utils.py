"""Shared Streamlit UI components for the ASD Video Analyzer app."""

from pathlib import Path
from typing import List
import pandas as pd

import streamlit as st

from config.config import DEFAULT_ASD_PROMPT


def get_default_asd_prompt() -> str:
    """Return the default ASD behavioral analysis prompt."""
    return DEFAULT_ASD_PROMPT


def parse_and_display_analysis(analysis_text: str) -> None:
    """Parse LLM analysis output and display signals as a table + narrative.
    
    Expects format with "SIGNALS:" section followed by pipe-delimited rows.
    """
    # Split by "SIGNALS:" marker
    if "SIGNALS:" not in analysis_text:
        # Fallback: just display as markdown if format is unexpected
        st.markdown(analysis_text)
        return
    
    parts = analysis_text.split("SIGNALS:", 1)
    signals_section = parts[1] if len(parts) > 1 else ""
    
    # Extract table rows (lines with pipes)
    rows = []
    narrative_lines = []
    
    for line in signals_section.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Check if this looks like a table row (contains pipes)
        if '|' in line:
            # Parse the row
            cells = [cell.strip() for cell in line.split('|')]
            # Filter out empty cells that might result from leading/trailing pipes
            cells = [c for c in cells if c]
            
            if len(cells) >= 4:
                # Expected format: Signal Name | Observed | Confidence | Note
                rows.append({
                    'Signal': cells[0],
                    'Observed': cells[1],
                    'Confidence': cells[2],
                    'Note': cells[3] if len(cells) > 3 else ''
                })
            elif len(cells) > 0:
                # Non-standard row, treat as narrative
                narrative_lines.extend(cells)
        else:
            # Non-table text, treat as narrative
            if line and not line.startswith('---'):
                narrative_lines.append(line)
    
    # Display signals as table
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
    
    # Display narrative
    narrative = '\n'.join(narrative_lines).strip()
    if narrative:
        st.markdown("### Clinical Observations")
        st.write(narrative)


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
