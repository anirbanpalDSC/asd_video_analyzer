# Project Guidelines

This workspace contains two small, mostly independent projects. Agents should pay attention to the root directories when editing or adding code.

## Code Style

* **Python (`asd_video_analyzer/`)**
  * Follow PEP 8 and idiomatic Python conventions.  Files are short and procedural; functions live in `src/` and configuration lives in `src/u_utils.py`.
  * Use type hints sparingly – the existing codebase is untyped but annotations are welcome if they make intent clearer.
  * External CLI tools are referenced via `shutil.which()` for portability.

## Architecture

* **asd_video_analyzer**
  * A Streamlit front‑end in `app.py` (currently empty) that orchestrates video uploads, transcription and AI analysis.
  * `src/` holds utility modules (`analyzer.py`, `processor.py`, `u_utils.py`) – the latter is a configuration hub.
  * The application depends on external tools (ffmpeg, whisper, ollama) and a local LLM server running on `OLLAMA_URL`.

## Build and Test

* **Python project**
  1. `cd asd_video_analyzer`.
  2. Create a virtual environment (`python -m venv venv` or equivalent).
  3. `pip install -r requirements.txt`.
  4. Run the app with `streamlit run app.py` or execute individual modules from the interpreter.
  5. There are no automated tests yet; add `pytest` fixtures if new modules warrant testing.

Agents should avoid inventing unrelated build systems or frameworks unless the user asks.

## Project Conventions

* Configuration values are centralized (Python in `u_utils.py`, PHP at the top of `index.php`).
* Video files live in `uploads/` (PHP) or are handled via Streamlit file upload widgets.
* When adding new features, respect the existing minimal dependency footprint; do not introduce heavy libraries without justification.

## Integration Points

* Both projects communicate with LLMs:
  * Python uses a local Ollama server (`OLLAMA_URL` environment) with a vision‑capable model or calls an external API (`https://gs1.cht77.com/api/chat`) via cURL.
* The Python project also relies on command‑line tools (`ffmpeg`, `whisper`).  Paths are configurable.

## Security

* Input is often treated as untrusted; PHP code sanitizes filenames and uses `htmlspecialchars()` when echoing user data.
* File uploads are restricted by extension and size; keep similar checks when adding new endpoints.
* Do not commit API keys or secrets to the repository.  Use configuration files or environment variables.

---

> 🛠 When editing code, make sure to operate in the correct subfolder. The workspace is not a monorepo; the two projects are logically separate despite sharing a common SSH session.

Please ask the user for clarification if a section above seems incomplete or if you need additional context.