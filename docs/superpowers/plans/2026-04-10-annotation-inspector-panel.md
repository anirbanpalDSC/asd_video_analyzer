# Annotation Inspector Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent right-column Annotation Inspector panel that shows per-frame specialized model output (gaze, pose, objects, language) when the user clicks 🔍 on a frame thumbnail.

**Architecture:** The main area splits into two `st.columns` — left holds the video player and transcript (unchanged), right holds the inspector. A 🔍 button is added under each frame thumbnail in the frame grid (below both columns). Clicking 🔍 sets `inspected_frame_idx` in session state; the inspector reads that key and renders the corresponding entry from `annotations.json`. Inspection is fully decoupled from frame selection for analysis.

**Tech Stack:** Streamlit, Python 3.10+, pathlib, json (stdlib only — no new dependencies)

---

## File Structure

| File | Change |
|------|--------|
| `src/ui_utils.py` | Add `format_frame_label()` (pure, testable) + `render_annotation_inspector()` (Streamlit renderer) |
| `app.py` | Two-column layout; load `annotations.json`; add 🔍 button per frame cell; call inspector in right column |
| `tests/test_ui_utils.py` | New — tests for `format_frame_label()` |

---

## Context you need

**Frame filename convention:** `thumb_00007.jpg` = frame index 7 (1-based). Timestamp in seconds = `(index - 1) / fps`. Extraction fps is always `2.0` (set in `processor.py`).

**`annotations.json` location:** `processed/<video_stem>/thumbs/annotations.json`. Dict keyed by filename: `{"thumb_00007.jpg": {"gaze": "...", "pose": "...", "objects": "...", "language": "..."}}`. A frame may be missing from the dict if it was not annotated (e.g. fps stride).

**Session state keys used in `app.py`:**
- `inspected_frame_idx` — `int | None` — index of the frame whose 🔍 was clicked (None = placeholder state)
- `frame_{idx}` — `bool` — existing checkbox state per frame (do not change)
- `frames_expander` — `bool` — existing expander open/close state (do not change)

**`app.py` current main-area structure (lines 308–520):**
```python
# video player
st.video(...)

# subheader + divider + transcript
st.subheader(...)
st.divider()
st.subheader("📝 Transcript")
st.text_area(...)   # or st.warning if no transcript

# frames expander (full-width)
with st.expander(...):
    # Select All / Clear All buttons
    # 5-column frame grid: checkbox + st.image per frame

# analysis section (full-width)
st.divider()
st.subheader("🔍 Behavioral Analysis")
...
```

The two-column split wraps only the video player + transcript block. The frames expander and analysis section remain full-width below both columns.

---

### Task 1: Add `format_frame_label()` and `render_annotation_inspector()` to `ui_utils.py`

**Files:**
- Modify: `src/ui_utils.py`
- Create: `tests/test_ui_utils.py`

- [ ] **Step 1: Create the test file with failing tests for `format_frame_label`**

```python
# tests/test_ui_utils.py
import pytest
from pathlib import Path
from src.ui_utils import format_frame_label


def test_format_frame_label_basic():
    # thumb_00001.jpg → frame 1, t = 0.0s
    assert format_frame_label("thumb_00001.jpg", fps=2.0) == "Frame 1 — t = 0.0s"


def test_format_frame_label_frame_7():
    # thumb_00007.jpg → frame 7, t = (7-1)/2.0 = 3.0s
    assert format_frame_label("thumb_00007.jpg", fps=2.0) == "Frame 7 — t = 3.0s"


def test_format_frame_label_frame_10():
    # thumb_00010.jpg → frame 10, t = (10-1)/2.0 = 4.5s
    assert format_frame_label("thumb_00010.jpg", fps=2.0) == "Frame 10 — t = 4.5s"


def test_format_frame_label_one_fps():
    # thumb_00003.jpg at 1.0 fps → frame 3, t = (3-1)/1.0 = 2.0s
    assert format_frame_label("thumb_00003.jpg", fps=1.0) == "Frame 3 — t = 2.0s"


def test_format_frame_label_unrecognised_name():
    # Non-standard filename: no digits parseable — falls back to filename
    result = format_frame_label("frame.jpg", fps=2.0)
    assert result == "frame.jpg"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/anirban/asd_video_analyzer
source venv/bin/activate
pytest tests/test_ui_utils.py -v
```

Expected: `ImportError` or `AttributeError` — `format_frame_label` does not exist yet.

- [ ] **Step 3: Add `format_frame_label()` to `src/ui_utils.py`**

Add immediately after the `get_default_asd_prompt()` function (after line 31):

```python
def format_frame_label(thumb_name: str, fps: float) -> str:
    """Return a human-readable label for a frame thumbnail.

    Example: 'thumb_00007.jpg' at 2.0 fps → 'Frame 7 — t = 3.0s'
    Falls back to the raw filename if the index cannot be parsed.
    """
    import re
    m = re.search(r"(\d+)", Path(thumb_name).stem)
    if not m:
        return thumb_name
    idx = int(m.group(1))
    t = (idx - 1) / fps
    # Format timestamp: show one decimal place, drop ".0" only if clean integer
    t_str = f"{t:.1f}s"
    return f"Frame {idx} — t = {t_str}"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ui_utils.py -v
```

Expected output:
```
tests/test_ui_utils.py::test_format_frame_label_basic PASSED
tests/test_ui_utils.py::test_format_frame_label_frame_7 PASSED
tests/test_ui_utils.py::test_format_frame_label_frame_10 PASSED
tests/test_ui_utils.py::test_format_frame_label_one_fps PASSED
tests/test_ui_utils.py::test_format_frame_label_unrecognised_name PASSED
5 passed
```

- [ ] **Step 5: Add `render_annotation_inspector()` to `src/ui_utils.py`**

Add at the end of `src/ui_utils.py`, after the `video_selector` / `show_video_info` block:

```python
# ---------------------------------------------------------------------------
# Annotation Inspector
# ---------------------------------------------------------------------------

_ANNOTATION_DOMAINS = [
    ("gaze",     "👁",  "Gaze"),
    ("pose",     "🦾", "Pose"),
    ("objects",  "📦", "Objects"),
    ("language", "🗣", "Language"),
]


def render_annotation_inspector(
    annotation: dict,
    thumb_path: Path,
    frame_label: str,
) -> None:
    """Render the annotation inspector panel for a single frame.

    annotation: dict with keys 'gaze', 'pose', 'objects', 'language' (any subset).
                Pass an empty dict when the frame has no annotations.json entry.
    thumb_path: Path to the frame JPEG thumbnail.
    frame_label: Human-readable label, e.g. 'Frame 7 — t = 3.0s'.
    """
    dark = st.session_state.get("theme", "light") == "dark"
    border_color = "#2e3450" if dark else "#d0d7e8"
    text_color   = "#c8d0e8" if dark else "#17191f"
    muted_color  = "#6b7280"
    bg_color     = "#1c2030" if dark else "#f8faff"

    st.markdown(f"#### 🔍 {frame_label}")
    st.image(str(thumb_path), width=220)

    if not annotation:
        st.caption("No annotations available for this frame.")
        return

    for key, icon, label in _ANNOTATION_DOMAINS:
        value = annotation.get(key, "")
        card_style = (
            f"background:{bg_color};border:1px solid {border_color};"
            f"border-radius:8px;padding:10px 14px;margin-bottom:8px;"
        )
        if value:
            text_html = f'<span style="color:{text_color};font-size:0.88em">{value}</span>'
        else:
            text_html = f'<span style="color:{muted_color};font-size:0.88em;font-style:italic">Not assessed</span>'

        st.markdown(
            f'<div style="{card_style}">'
            f'<span style="font-weight:600;font-size:0.82em;color:{muted_color};text-transform:uppercase;'
            f'letter-spacing:0.05em">{icon} {label}</span><br>{text_html}'
            f'</div>',
            unsafe_allow_html=True,
        )
```

- [ ] **Step 6: Run full test suite to confirm nothing broke**

```bash
pytest tests/ -v
```

Expected: all existing tests still pass + 5 new `test_ui_utils` tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/ui_utils.py tests/test_ui_utils.py
git commit -m "feat: add format_frame_label and render_annotation_inspector to ui_utils"
```

---

### Task 2: Update `app.py` with two-column layout and 🔍 buttons

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add `inspected_frame_idx` to session state initialisation**

In `app.py`, find the block that initialises frame-related session state (around line 357):

```python
    if 'selected_frames_indices' not in st.session_state:
        st.session_state.selected_frames_indices = set()
    if "frames_expander" not in st.session_state:
        st.session_state["frames_expander"] = True
```

Add one line after the existing two:

```python
    if 'selected_frames_indices' not in st.session_state:
        st.session_state.selected_frames_indices = set()
    if "frames_expander" not in st.session_state:
        st.session_state["frames_expander"] = True
    if "inspected_frame_idx" not in st.session_state:
        st.session_state["inspected_frame_idx"] = None
```

- [ ] **Step 2: Load `annotations.json` once after `get_video_info()`**

Find the line `info = processor.get_video_info(selected_video)` (around line 305). Add immediately after it:

```python
    # Load annotations for the inspector (small JSON file, read once per rerun)
    import json as _json
    _ann_path = (
        info['thumbs'][0].parent / "annotations.json"
        if info['thumbs'] else None
    )
    _all_annotations: dict = {}
    if _ann_path and _ann_path.exists():
        try:
            _all_annotations = _json.loads(_ann_path.read_text(encoding="utf-8"))
        except Exception:
            _all_annotations = {}
```

- [ ] **Step 3: Wrap video player + transcript in the left column**

Find the block (around lines 315–348):

```python
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
        ...
    else:
        st.text_area(
            "Audio transcript:",
            value=info['transcript'],
            height=150,
            disabled=True,
            label_visibility="collapsed",
        )
```

Replace the entire block above (from `video_path = UPLOADS_DIR / selected_video` through the closing of the transcript section, ending at the `if not info['thumbs']:` guard) with:

```python
    # ── Two-column layout: video+transcript | annotation inspector ──────────
    _left_col, _right_col = st.columns([45, 55])

    with _left_col:
        video_path = UPLOADS_DIR / selected_video
        if video_path.exists():
            st.video(str(video_path), start_time=0)

        st.subheader(f"Video: {selected_video[:40]}...")
        st.divider()
        st.subheader("📝 Transcript")
        if info.get('transcript') is None:
            import shutil as _shutil
            if not _shutil.which("whisper"):
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
            st.text_area(
                "Audio transcript:",
                value=info['transcript'],
                height=150,
                disabled=True,
                label_visibility="collapsed",
            )

    with _right_col:
        _inspected_idx = st.session_state.get("inspected_frame_idx")
        if _inspected_idx is None or not info['thumbs'] or _inspected_idx >= len(info['thumbs']):
            st.info("Click 🔍 on any frame below to inspect its annotations.")
        else:
            _thumb = info['thumbs'][_inspected_idx]
            _annotation = _all_annotations.get(_thumb.name, {})
            _label = ui_utils.format_frame_label(_thumb.name, fps=2.0)
            ui_utils.render_annotation_inspector(_annotation, _thumb, _label)
```

- [ ] **Step 4: Add 🔍 button under each frame thumbnail in the frame grid**

Find the frame rendering block inside the expander (around lines 416–436):

```python
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
```

Replace with:

```python
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

                if st.button("🔍", key=f"inspect_{idx}", use_container_width=True, help="Inspect annotations"):
                    st.session_state["inspected_frame_idx"] = idx
                    st.rerun()
```

- [ ] **Step 5: Clear `inspected_frame_idx` when the selected video changes**

Find the block that clears frame selection state when the video changes (around lines 236–243):

```python
    if selected_video != st.session_state.get('_last_video'):
        st.session_state['_last_video'] = selected_video
        st.session_state['selected_frames_indices'] = set()
        st.session_state.pop('analysis_result', None)
        st.session_state['frames_expander'] = True
        # Clear all individual frame checkbox keys
        for k in [k for k in st.session_state if k.startswith('frame_')]:
            del st.session_state[k]
```

Add one line to also reset the inspector:

```python
    if selected_video != st.session_state.get('_last_video'):
        st.session_state['_last_video'] = selected_video
        st.session_state['selected_frames_indices'] = set()
        st.session_state.pop('analysis_result', None)
        st.session_state['frames_expander'] = True
        st.session_state['inspected_frame_idx'] = None
        # Clear all individual frame checkbox keys
        for k in [k for k in st.session_state if k.startswith('frame_')]:
            del st.session_state[k]
```

- [ ] **Step 6: Remove the now-duplicate `import shutil` in the transcript block**

The existing code below line ~328 has a local `import shutil` inside an `if` block. Since we moved the transcript block into `_left_col` and used `import shutil as _shutil` there, search for any remaining bare `import shutil` inside the transcript section that's now duplicated and remove it if present. (If the original code had `import shutil` at the top of the function, leave it alone.)

- [ ] **Step 7: Verify the app runs without errors**

```bash
cd /home/anirban/asd_video_analyzer
source venv/bin/activate
venv/bin/python -c "
import sys
sys.path.insert(0, '.')
from src import ui_utils, processor, analyzer, theme
from config.config import UPLOADS_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS, ensure_dirs, ASD_SIGNAL_REFERENCE
print('All imports OK')
"
```

Expected:
```
All imports OK
```

- [ ] **Step 8: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
git add app.py
git commit -m "feat: add annotation inspector panel with two-column layout and inspect buttons"
```

---

## Manual Verification (after both tasks)

1. Open the Streamlit app in the browser
2. Select a previously processed video — the main area should now show two columns: video+transcript on the left, *"Click 🔍 on any frame below to inspect its annotations."* on the right
3. Scroll to the frames grid — each frame should have a 🔍 button below the thumbnail
4. Click 🔍 on any frame — the right column should update to show the frame label, thumbnail, and four annotation cards (Gaze, Pose, Objects, Language)
5. Click a different frame's 🔍 — the inspector updates; the previously selected checkboxes are unaffected
6. Click Select All — frame checkboxes all tick; inspector is unchanged
7. Switch to a different video — inspector resets to placeholder state
8. Click 🔍 on a frame with no annotations entry — right column shows *"No annotations available for this frame."*
