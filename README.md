# ASD Video Analyzer

A Streamlit web application for analyzing video clips for behavioral signals associated with Autism Spectrum Disorder (ASD). The tool processes uploaded or linked videos through a multimodal AI pipeline, producing a structured signal table and a clinical observation narrative for each session.

---

## Features

- **Flexible video input** — upload local files (MP4, MOV, AVI, MKV, WEBM, up to 512 MB) or paste a YouTube / Facebook URL for automatic download via `yt-dlp`
- **Automated preprocessing** — `ffmpeg` extracts audio to MP3 and captures JPEG thumbnails at 2 fps; `whisper` transcribes the audio (CUDA with CPU fallback)
- **Interactive frame selection** — browse extracted frames in a 5-column grid; select individual frames or use Select All / Clear All
- **Multimodal LLM analysis** — selected frames (base64-encoded) and the audio transcript are sent to a remote vision-capable model (`gemma3:27b-it-fp16`) via an Ollama-compatible API
- **Structured output** — the model response is parsed into a 10-signal behavioral table (Observed / Confidence / Note) plus a 3–5 sentence clinical narrative
- **Customizable prompt** — the default ASD prompt can be edited in-app before running analysis
- **Signal reference sidebar** — in-app reference card describing each of the 10 ASD signal categories
- **Idempotent processing** — already-processed videos are not reprocessed unless forced

---

## ASD Signal Categories

| Domain | Signal |
|---|---|
| Social | Absence or Avoidance of Eye Contact |
| Social | Aggressive Behavior |
| Social | Non-Responsiveness to Verbal Interaction |
| Social | Non-Typical Language |
| RRB | Hyper- or Hyporeactivity to Sensory Input |
| RRB | Object Lining-Up |
| RRB | Self-Hitting or Self-Injurious Behavior |
| RRB | Self-Spinning or Spinning Objects |
| RRB | Upper Limb Stereotypies |
| — | Background (not applicable) |

*RRB = Restricted and Repetitive Behaviors*

---

## Requirements

### System dependencies (install separately)

| Tool | Purpose |
|---|---|
| `ffmpeg` | Audio extraction and frame capture |
| `openai-whisper` | Audio transcription (CLI: `whisper`) |
| `yt-dlp` | YouTube / Facebook video download |

### Python dependencies

```
streamlit>=1.35.0
requests>=2.28.0
Pillow>=9.3.0
openai-whisper>=20240314
pandas>=1.5.0
yt-dlp>=2024.01.01
```

---

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run locally

```bash
streamlit run app.py
```

---

## Architecture

```
app.py                  # Streamlit entry point — UI layout and session state
config/
  config.py             # Central configuration: paths, API URL, ASD prompt, signal reference
src/
  processor.py          # Video pipeline: ffmpeg audio/frame extraction, whisper transcription, yt-dlp download
  analyzer.py           # LLM API call: builds multimodal payload, sends to API_URL, returns response text
  ui_utils.py           # UI helpers: parses pipe-delimited LLM output into DataFrame + narrative
  u_utils.py            # CLI tool path resolution (FFMPEG_CMD, WHISPER_CMD) via shutil.which()
uploads/                # Raw uploaded/downloaded video files (gitignored)
processed/              # Pipeline artifacts per video: MP3, thumbs/*.jpg, transcript .txt (gitignored)
```

**Data flow:**

1. Video is saved to `uploads/` (file upload) or downloaded there by `yt-dlp` (URL input)
2. `processor.process_video()` runs: `ffmpeg` → MP3 + JPEG thumbnails; `whisper` → `.txt` transcript
3. Artifacts land in `processed/<video_stem>/` and are read back by `get_video_info()`
4. User selects frames in the UI; "Run Analysis" base64-encodes frames, appends transcript, and POSTs to `API_URL`
5. The LLM response is parsed by `parse_and_display_analysis()` and rendered as a table + narrative

---

## Deployment

The app is served at:

| Environment | URL |
|---|---|
| Production | https://ns.cht77.com |
| Development | https://ns.cht77.com/dev |

Apache acts as a reverse proxy with WebSocket support (`mod_proxy_wstunnel`). Streamlit runs as a systemd service on internal ports (`8501` production, `8502` dev).

### CI/CD

GitHub Actions automates deployment:

| Branch | Action |
|---|---|
| `main` | Deploys to `/opt/asd-analyzer` → restarts `asd-analyzer.service` |
| `dev` | Deploys to `/opt/asd-analyzer-dev` → restarts `asd-analyzer-dev.service` |

Deployments preserve `uploads/` and `processed/` on the server.

**Required repository secrets:**

| Secret | Value |
|---|---|
| `DEPLOY_HOST` | `ns.cht77.com` |
| `DEPLOY_USER` | SSH username on the server |
| `DEPLOY_SSH_KEY` | Private SSH key with access to the server |

---

## Configuration

All runtime configuration lives in `config/config.py`:

| Setting | Default | Description |
|---|---|---|
| `API_URL` | `https://gs1.cht77.com/api/chat` | Ollama-compatible LLM endpoint |
| `MAX_FILE_SIZE` | 512 MB | Maximum upload size |
| `ALLOWED_EXTENSIONS` | mp4, mov, avi, mkv, webm | Accepted video formats |
| `UPLOADS_DIR` | `uploads/` | Raw video storage |
| `PROCESSED_DIR` | `processed/` | Pipeline artifact storage |

The LLM model is set in `src/analyzer.py` (`gemma3:27b-it-fp16`). The whisper model is set in `src/processor.py` (`base`; change to `large` for higher accuracy).

---

## Disclaimer

This tool is intended to assist researchers and clinicians by surfacing potential behavioral signals in video data. It is **not a diagnostic instrument**. All outputs should be reviewed by a qualified professional. No clinical decisions should be made solely on the basis of this tool's output.

---

## Release Notes

### v1.0.0 — 2026-03-14

Initial public release.

- Streamlit single-page application with sidebar-based video management
- Support for local file upload and YouTube / Facebook URL download via `yt-dlp`
- Automated ffmpeg pipeline: audio extraction (MP3) and frame capture (JPEG at 2 fps)
- Whisper-based audio transcription with automatic CUDA → CPU fallback
- Interactive 5-column frame grid with Select All / Clear All controls
- Multimodal analysis via remote `gemma3:27b-it-fp16` model (Ollama-compatible API)
- 10-category ASD behavioral signal schema (Social domain + RRB domain)
- Structured output: pipe-delimited signal table parsed to a Pandas DataFrame + clinical narrative
- Customizable analysis prompt with in-app editor
- ASD signal reference card in sidebar
- Idempotent video processing (skips already-processed videos)
- GitHub Actions CI/CD for automated deployment to production (`main`) and development (`dev`) environments
- Apache reverse proxy configuration for `ns.cht77.com` (production) and `ns.cht77.com/dev`
