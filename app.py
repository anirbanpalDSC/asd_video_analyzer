import os
from pathlib import Path
from typing import List, Optional

import streamlit as st

from config.config import (
    UPLOADS_DIR,
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS,
    ensure_dirs,
    ASD_SIGNAL_REFERENCE,
)
from src import processor, analyzer, ui_utils, theme

# Configure page layout
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------------------
# helpers used by the app
# ---------------------------------------------------------------------------

def save_uploaded_file(uploaded) -> str:
    """Persist an uploaded file to the uploads directory, returning the saved name."""
    ensure_dirs()
    if not uploaded:
        return ""
    fname = uploaded.name
    # enforce extension
    if Path(fname).suffix.lstrip('.').lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Invalid file type")
    if uploaded.size > MAX_FILE_SIZE:
        raise ValueError("File exceeds maximum size")
    import uuid

    unique = f"{Path(fname).stem}_{uuid.uuid4().hex}{Path(fname).suffix}"
    dest = UPLOADS_DIR / unique
    with open(dest, 'wb') as f:
        f.write(uploaded.getbuffer())
    return unique


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    # ── Theme injection ────────────────────────────────────────────────────
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    st.markdown(theme.get_theme_css(st.session_state.theme), unsafe_allow_html=True)

    st.title("ASD Video Analyzer")

    # =========================================================================
    # SIDEBAR: Controls & Upload
    # =========================================================================
    with st.sidebar:
        # Theme toggle
        _icon = "☀️" if st.session_state.theme == "dark" else "🌙"
        _label = f"{_icon} Switch to {'light' if st.session_state.theme == 'dark' else 'dark'} mode"
        if st.button(_label, use_container_width=True, key="theme_toggle"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()

        st.divider()
        _h_col, _r_col = st.columns([3, 1])
        with _h_col:
            st.header("📁 Upload & Process")
        with _r_col:
            st.write("")  # vertical alignment nudge
            if st.button("🔄", use_container_width=True, help="Reset / Clear selection"):
                st.session_state.selected_video = None
                st.session_state.selected_frames_indices = set()
                st.session_state.processed_upload_name = None
                st.session_state.pop("analysis_result", None)
                st.rerun()

        st.divider()
        
        # Tabs for upload method
        tab_upload, tab_link = st.tabs(["📤 Upload File", "🔗 Paste Link"])
        
        with tab_upload:
            # File uploader in sidebar; persist key so state survives reruns
            uploaded = st.file_uploader("Upload a video", type=list(ALLOWED_EXTENSIONS), key="uploader")

            # Only process when a new file arrives (compare by original name)
            if uploaded is not None:
                prev = st.session_state.get("processed_upload_name")
                if prev != uploaded.name:
                    try:
                        saved_name = save_uploaded_file(uploaded)
                        st.success(f"✓ Uploaded: {saved_name[:30]}...")
                        with st.spinner("Processing video..."):
                            processor.process_video(UPLOADS_DIR / saved_name)
                        # Clear previous analysis and frame selection
                        st.session_state.selected_frames_indices = set()
                        st.session_state["frames_expander"] = True
                        st.session_state.selected_video = saved_name
                        # remember this upload so we don't loop
                        st.session_state.processed_upload_name = uploaded.name
                        
                        # Get and display transcript immediately after upload
                        info = processor.get_video_info(saved_name)
                        if info.get('transcript') is None:
                            st.divider()
                            import shutil
                            if not shutil.which("whisper"):
                                st.warning(
                                    "Transcript not available because the `whisper` CLI tool isn't installed or not found in PATH. "
                                    "Install it or configure `u_utils.WHISPER_CMD`."
                                )
                            else:
                                st.warning(
                                    "Transcript not available. The video audio may not be extractable or transcription failed."
                                )
                        else:
                            st.divider()
                            st.subheader("📝 Transcript")
                            with st.expander("View transcript", expanded=True):
                                st.text_area(
                                    "Audio transcript:", 
                                    value=info['transcript'], 
                                    height=150,
                                    disabled=True,
                                    label_visibility="collapsed"
                                )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {str(e)}")
                        # clear cache so user can retry
                        st.session_state.processed_upload_name = None
        
        with tab_link:
            st.write("Paste a YouTube or Facebook video link:")
            video_url = st.text_input("Video URL", placeholder="https://www.youtube.com/watch?v=...", key="video_link_input")
            
            if st.button("📥 Download & Process", use_container_width=True, key="download_btn"):
                if not video_url or not video_url.strip():
                    st.error("Please enter a valid video URL.")
                else:
                    with st.spinner("Downloading video..."):
                        saved_name = processor.download_video_from_url(video_url)
                    
                    if saved_name is None:
                        st.error(
                            "❌ Failed to download video. The video may not be available, "
                            "or the URL is invalid. Ensure the link is publicly accessible."
                        )
                    else:
                        st.success(f"✓ Downloaded: {saved_name[:30]}...")
                        with st.spinner("Processing video..."):
                            processor.process_video(UPLOADS_DIR / saved_name)
                        
                        # Clear previous analysis and frame selection
                        st.session_state.selected_frames_indices = set()
                        st.session_state["frames_expander"] = True
                        st.session_state.selected_video = saved_name

                        # Get and display transcript immediately after processing
                        info = processor.get_video_info(saved_name)
                        if info.get('transcript') is None:
                            st.divider()
                            import shutil
                            if not shutil.which("whisper"):
                                st.warning(
                                    "Transcript not available because the `whisper` CLI tool isn't installed or not found in PATH. "
                                    "Install it or configure `u_utils.WHISPER_CMD`."
                                )
                            else:
                                st.warning(
                                    "Transcript not available. The video audio may not be extractable or transcription failed."
                                )
                        else:
                            st.divider()
                            st.subheader("📝 Transcript")
                            with st.expander("View transcript", expanded=True):
                                st.text_area(
                                    "Audio transcript:", 
                                    value=info['transcript'], 
                                    height=150,
                                    disabled=True,
                                    label_visibility="collapsed"
                                )
                        st.rerun()
        
        st.divider()
        
        # Video selection from history
        videos = processor.list_uploads()
        if videos:
            st.subheader("Recent Videos")
            selected = st.selectbox(
                "Choose a video", 
                videos,
                key="sidebar_video_select",
                index=None,
                placeholder="Select a video..."
            )
            if selected and selected != st.session_state.get("selected_video"):
                st.session_state.selected_video = selected
                st.session_state.pop("analysis_result", None)

            # Delete button for currently selected video
            current = st.session_state.get('selected_video')
            if current:
                st.divider()
                st.caption(f"Selected: `{current[:35]}...`" if len(current) > 35 else f"Selected: `{current}`")
                if st.button("🗑️ Delete this video", use_container_width=True, type="secondary"):
                    st.session_state['confirm_delete'] = True

                if st.session_state.get('confirm_delete'):
                    st.warning("This will permanently delete the video, audio, frames, and transcript.")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Yes, delete", use_container_width=True, type="primary"):
                            processor.delete_video(current)
                            st.session_state.selected_video = None
                            st.session_state.selected_frames_indices = set()
                            st.session_state.processed_upload_name = None
                            st.session_state['confirm_delete'] = False
                            st.rerun()
                    with col_no:
                        if st.button("Cancel", use_container_width=True):
                            st.session_state['confirm_delete'] = False
                            st.rerun()
    
    # =========================================================================
    # MAIN AREA: Video Analysis
    # =========================================================================
    
    selected_video = st.session_state.get('selected_video')

    # Clear frame selection state whenever the active video changes
    if selected_video != st.session_state.get('_last_video'):
        st.session_state['_last_video'] = selected_video
        st.session_state['selected_frames_indices'] = set()
        st.session_state.pop('analysis_result', None)
        st.session_state['frames_expander'] = True
        # Clear all individual frame checkbox keys
        for k in [k for k in st.session_state if k.startswith('frame_')]:
            del st.session_state[k]

    # Signal reference and release notes — always visible in sidebar
    with st.sidebar:
        st.divider()
        st.write("")
        st.subheader("📚 Signal Reference")
        st.write("")
        with st.expander("ASD Signal Categories", expanded=False):
            for signal, description in ASD_SIGNAL_REFERENCE.items():
                st.write(f"**{signal}**")
                st.write(description)
                st.divider()

        st.write("")
        st.divider()
        st.write("")
        st.subheader("📋 Release Notes")
        st.write("")
        with st.expander("What's new", expanded=False):
            st.markdown("""
**v0.8** — Specialized model annotation pipeline
- L2CS-Net gaze estimation injected as frame-level annotations (Signal 1)
- MediaPipe Pose + Hands posture geometry annotations (Signals 7, 8, 9)
- YOLOv8m object arrangement detection (Signal 6)
- Whisper word-timestamp language alignment per frame (Signals 4, 5)
- VLM prompt now includes FRAME_ANNOTATIONS with quantitative measurements
- Annotation cached in annotations.json — one-time cost per video

**v0.7** — UI refinements
- Video player resized to compact fixed width
- Sidebar expander content has solid white/dark background
- Signal Reference and Release Notes always visible in sidebar
- Fullscreen button removed from frame thumbnails
- Extra spacing around sidebar sections

**v0.6** — Frame selection limit
- Max 15 frames per analysis enforced with modal warning
- Select All blocked when total frames exceed limit

**v0.5** — Streaming & reliability
- Analysis no longer hangs; live token counter during generation
- Hard 300s timeout prevents infinite waits

**v0.4** — UI polish
- Light/dark mode fully consistent across all components
- Analysis results persist across theme switches
- CSV download for analysis table

**v0.3** — Frame selector UX
- Expander stays open while selecting frames
- Shift-click to select a range of frames
- Reset button no longer overlaps header

**v0.2** — Analysis display
- Per-frame signal detection (FRAME_DETECTIONS format)
- Frequency-based confidence (High / Medium / Low)
- Clinical narrative section

**v0.1** — Initial release
- Video upload & YouTube / Facebook link download
- Audio transcription via Whisper
- Behavioral signal analysis via local LLM (Ollama)
""")

    if not selected_video:
        st.info("👈 Upload a video using the sidebar to get started.")
        return

    # Get video info
    info = processor.get_video_info(selected_video)

    # Show video player with original video + audio (consistent width for both upload and download)
    video_path = UPLOADS_DIR / selected_video
    if video_path.exists():
        st.video(str(video_path), start_time=0)
    
    # Main content: Frame selection and analysis
    st.subheader(f"Video: {selected_video[:40]}...")
    
    # show transcript area no matter what, so user always knows status
    st.divider()
    st.subheader("📝 Transcript")
    if info.get('transcript') is None:
        # detect if whisper binary is missing
        import shutil

        if not shutil.which("whisper"):
            st.warning(
                "Transcript not available because the `whisper` CLI tool isn't installed or not found in PATH. "
                "Install it or set `u_utils.WHISPER_CMD` to the correct executable."
            )
        else:
            st.warning(
                "Transcript not available. The video may contain no audio or the audio could not be processed. "
                "Make sure the file is valid and retry."
            )
    else:
        # transcript may be empty string; show anyway
        st.text_area(
            "Audio transcript:",
            value=info['transcript'],
            height=150,
            disabled=True,
            label_visibility="collapsed",
        )

    if not info['thumbs']:
        st.warning("⏳ Video is still processing. Please wait a moment and refresh.")
        return
    
    FRAME_LIMIT = 15

    # Initialize session state for frame selection if not exists
    if 'selected_frames_indices' not in st.session_state:
        st.session_state.selected_frames_indices = set()
    if "frames_expander" not in st.session_state:
        st.session_state["frames_expander"] = True

    @st.dialog("Frame limit reached")
    def _show_frame_limit_dialog():
        st.warning(
            f"Frame selection is limited to **{FRAME_LIMIT} frames** per analysis. "
            "Sending too many frames at once can overload the model and cause timeouts. "
            "Please deselect some frames before adding more."
        )
        if st.button("OK", type="primary", use_container_width=True):
            st.rerun()

    def _make_frame_callback(frame_idx, total_frames):
        def _callback():
            st.session_state["frames_expander"] = True
            if st.session_state.get(f"frame_{frame_idx}", False):
                n = sum(1 for i in range(total_frames) if st.session_state.get(f"frame_{i}", False))
                if n > FRAME_LIMIT:
                    st.session_state[f"frame_{frame_idx}"] = False
                    st.session_state["_show_frame_limit"] = True
        return _callback

    if st.session_state.pop("_show_frame_limit", False):
        _show_frame_limit_dialog()

    n_selected = sum(1 for i in range(len(info['thumbs'])) if st.session_state.get(f"frame_{i}", False))
    expander_label = f"🎞️ Frames — {len(info['thumbs'])} extracted, {n_selected} selected"
    with st.expander(expander_label, expanded=st.session_state["frames_expander"]):
        # Select All / Deselect All buttons
        col1, col2, col3 = st.columns([1, 1, 6])
        with col1:
            if st.button("✓ Select All", use_container_width=True):
                if len(info['thumbs']) > FRAME_LIMIT:
                    st.session_state["frames_expander"] = True
                    st.session_state["_show_frame_limit"] = True
                    st.rerun()
                else:
                    all_indices = set(range(len(info['thumbs'])))
                    st.session_state.selected_frames_indices = all_indices
                    for idx in all_indices:
                        st.session_state[f"frame_{idx}"] = True
                    st.session_state["frames_expander"] = True
                    st.rerun()
        with col2:
            if st.button("✗ Clear All", use_container_width=True):
                st.session_state.selected_frames_indices = set()
                for idx in range(len(info['thumbs'])):
                    st.session_state[f"frame_{idx}"] = False
                st.session_state["frames_expander"] = True
                st.rerun()
        with col3:
            st.caption(f"Max {FRAME_LIMIT} frames per analysis to ensure reliable results.")

        # Display frames in a grid of 5 columns
        cols_per_row = 5
        total_thumbs = len(info['thumbs'])
        for idx, thumb_path in enumerate(info['thumbs']):
            if idx % cols_per_row == 0:
                cols = st.columns(cols_per_row)

            col_idx = idx % cols_per_row
            with cols[col_idx]:
                key = f"frame_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = idx in st.session_state.selected_frames_indices

                is_selected = st.checkbox(
                    f"Frame {idx + 1}", key=key,
                    on_change=_make_frame_callback(idx, total_thumbs)
                )

                if is_selected:
                    st.session_state.selected_frames_indices.add(idx)
                else:
                    st.session_state.selected_frames_indices.discard(idx)

                st.image(str(thumb_path), width="stretch")

    st.divider()
    
    # Analysis section
    st.subheader("🔍 Behavioral Analysis")
    
    # Get selected frames paths
    selected_frames = [
        info['thumbs'][idx]
        for idx in sorted(st.session_state.selected_frames_indices)
        if idx < len(info['thumbs'])
    ]
    
    if not selected_frames:
        st.warning("Select at least one frame to analyze.")
        return
    
    st.write(f"**Frames to analyze:** {len(selected_frames)} selected")
    
    # Prompt customization (with ASD default)
    default_prompt = ui_utils.get_default_asd_prompt()
    
    with st.expander("Customize Analysis Prompt", expanded=False):
        user_prompt = st.text_area(
            "Analysis Prompt:",
            value=default_prompt,
            height=300,
            key="user_prompt"
        )
    
    # Run analysis
    if st.button("▶️ Run Analysis", type="primary"):
        if len(selected_frames) == 0:
            st.error("Please select at least one frame.")
        else:
            st.session_state["frames_expander"] = False
            st.session_state.pop("analysis_result", None)
            try:
                import threading, time as _time
                prompt_arg = user_prompt if user_prompt != default_prompt else None
                stream = analyzer.analyze_stream(
                    selected_video,
                    user_prompt=prompt_arg,
                    selected_thumb_paths=selected_frames,
                    transcript=info['transcript'],
                )

                # Collect stream in background thread; poll from main thread
                # so Streamlit can update the status widget live.
                _tokens: list = []
                _err: list = [None]
                _done: list = [False]

                def _collect():
                    try:
                        for tok in stream:
                            _tokens.append(tok)
                    except Exception as exc:
                        _err[0] = exc
                    finally:
                        _done[0] = True

                threading.Thread(target=_collect, daemon=True).start()

                status = st.empty()
                _start = _time.time()
                while not _done[0]:
                    elapsed = int(_time.time() - _start)
                    n = len(_tokens)
                    if n == 0:
                        status.info(f"Uploading frames & waiting for model… ({elapsed}s)")
                    else:
                        status.info(f"Generating… {n} tokens received ({elapsed}s)")
                    _time.sleep(0.5)

                status.empty()
                if _err[0]:
                    raise _err[0]
                result = "".join(_tokens).strip()
                st.session_state["analysis_result"] = result
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")

    # Always render stored result (survives theme toggles and other reruns)
    if st.session_state.get("analysis_result"):
        st.subheader("Analysis Results")
        ui_utils.parse_and_display_analysis(st.session_state["analysis_result"])


if __name__ == '__main__':
    main()
