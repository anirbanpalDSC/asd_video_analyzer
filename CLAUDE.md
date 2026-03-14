# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Setup:**
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

**Run the app:**
```bash
streamlit run app.py
```

**System dependencies** (must be installed separately):
- `ffmpeg` — video/audio processing
- `whisper` (openai-whisper) — audio transcription; auto-detected from PATH or Python module
- `ollama` — local LLM server (must be running with a vision-capable model)

There are no automated tests; add `pytest` fixtures if new modules warrant testing.

## Architecture

The app is a single-page Streamlit application (`app.py`) for analyzing video clips for ASD (Autism Spectrum Disorder) behavioral signals.

**Data flow:**
1. User uploads a video file or pastes a YouTube/Facebook URL (via `yt-dlp`)
2. `processor.process_video()` runs the pipeline: `ffmpeg` extracts audio to MP3, `ffmpeg` extracts frames as JPEG thumbnails, `whisper` transcribes the audio
3. Processed artifacts are stored under `processed/<video_stem>/` (MP3, `thumbs/thumb_*.jpg`, transcript `.txt`)
4. User selects frames in the UI; clicking "Run Analysis" sends base64-encoded frames + transcript to the remote LLM API
5. The LLM response is parsed and displayed as a structured signals table + clinical narrative

**Module responsibilities:**
- `config/config.py` — all configuration: paths (`UPLOADS_DIR`, `PROCESSED_DIR`), `API_URL`, `DEFAULT_ASD_PROMPT`, `ASD_SIGNAL_REFERENCE`, `MAX_FILE_SIZE`, `ALLOWED_EXTENSIONS`
- `src/u_utils.py` — CLI tool paths (`FFMPEG_CMD`, `WHISPER_CMD`) resolved via `shutil.which()` with fallbacks
- `src/processor.py` — video pipeline functions (`process_video`, `get_video_info`, `list_uploads`, `download_video_from_url`)
- `src/analyzer.py` — LLM API call: builds the multimodal message payload with base64 images and sends to `API_URL`; model is hardcoded as `gemma3:27b-it-fp16`
- `src/ui_utils.py` — Streamlit UI helpers: `parse_and_display_analysis()` parses pipe-delimited LLM output into a DataFrame

**Key conventions:**
- `process_video()` is idempotent: skips re-processing if the processed folder already exists (unless `force=True`)
- Whisper transcription uses `cuda` first, falls back to `cpu`; failure is non-fatal
- The LLM API (`API_URL = https://gs1.cht77.com/api/chat`) expects an Ollama-compatible chat payload (`{"model": ..., "messages": [...], "stream": false}`)
- Configuration lives in `config/config.py`; CLI tool paths live in `src/u_utils.py`
- Avoid introducing heavy libraries without justification; keep the dependency footprint minimal
