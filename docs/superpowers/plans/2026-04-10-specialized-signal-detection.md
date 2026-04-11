# Specialized Signal Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pre-processing annotation layer that runs L2CS-Net (gaze), MediaPipe Pose+Hands (motor), YOLOv8m (objects), and frame-aligned Whisper NLP (language) on each thumbnail at processing time, caches results in `annotations.json`, and injects them as a `FRAME_ANNOTATIONS:` block into the Gemma3 VLM prompt at analysis time.

**Architecture:** New `src/annotator.py` owns all model loading and inference. `src/processor.py` calls `annotate_frames()` after thumbnail extraction and writes `annotations.json`. `src/analyzer.py` loads that JSON and injects per-frame annotations into the prompt. `config/config.py` gains `ANNOTATION_FPS`. No changes to `ui_utils.py`, `app.py`, or output format.

**Tech Stack:** Python, l2cs (gaze), mediapipe (pose+hands), ultralytics/YOLOv8 (objects), openai-whisper word timestamps, gdown (weight download), torch/CUDA

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/annotator.py` | **Create** | All model loading, inference, and natural language generation |
| `tests/test_annotator.py` | **Create** | Unit tests for pure geometry and NLP functions |
| `src/processor.py` | **Modify** | Call `annotate_frames()` after thumbnails; write `annotations.json`; add `transcribe_mp3_with_timestamps()` |
| `src/analyzer.py` | **Modify** | Load `annotations.json`; inject `FRAME_ANNOTATIONS:` block into prompt (both `analyze()` and `analyze_stream()`) |
| `config/config.py` | **Modify** | Add `ANNOTATION_FPS = 2.0`; add `FRAME_ANNOTATIONS` instructions to `DEFAULT_ASD_PROMPT` |
| `requirements.txt` | **Modify** | Add l2cs, mediapipe, ultralytics, gdown |
| `models/` | **Create dir** | Stores downloaded L2CS-Net weights |

---

### Task 1: Install dependencies and download model weights

**Files:**
- Modify: `requirements.txt`
- Create dir: `models/`

- [ ] **Step 1: Install Python packages**

```bash
source venv/bin/activate
pip install l2cs mediapipe ultralytics gdown
```

Expected: all four packages install without error. `torch` and `torchvision` should already be present (Whisper depends on torch); confirm:

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

Expected: `True`

- [ ] **Step 2: Download L2CS-Net weights**

```bash
mkdir -p models
source venv/bin/activate
python -c "
import gdown, pathlib
dest = pathlib.Path('models/L2CSNet_gaze360.pkl')
if not dest.exists():
    gdown.download(id='1V7r9C7qn0umapK8VvWDAtNWYGlCRtcEL', output=str(dest), quiet=False)
    print('Downloaded:', dest.stat().st_size, 'bytes')
else:
    print('Already present')
"
```

Expected: file `models/L2CSNet_gaze360.pkl` (~200 MB) created.

- [ ] **Step 3: Add packages to requirements.txt**

Open `requirements.txt` and append:

```
l2cs>=0.1.0
mediapipe>=0.10.0
ultralytics>=8.0.0
gdown>=4.7.0
```

- [ ] **Step 4: Verify imports**

```bash
source venv/bin/activate
python -c "
from l2cs import Pipeline
import mediapipe as mp
from ultralytics import YOLO
print('All imports OK')
"
```

Expected: `All imports OK`

- [ ] **Step 5: Commit**

```bash
git add requirements.txt models/.gitkeep
git commit -m "feat: add specialized model dependencies and L2CS-Net weights"
```

---

### Task 2: Add ANNOTATION_FPS to config/config.py

**Files:**
- Modify: `config/config.py`

- [ ] **Step 1: Add ANNOTATION_FPS constant**

In `config/config.py`, after the `API_URL` line, add:

```python
# Frames per second to annotate with specialized models.
# Lower this to reduce processing time for long videos (e.g. 1.0 for 60-min videos).
# Must be <= the thumbnail extraction fps (2.0). Non-annotated thumbnails are still
# displayed and selectable; they simply have no FRAME_ANNOTATIONS entry in the prompt.
ANNOTATION_FPS: float = 2.0
```

- [ ] **Step 2: Add GAZE_WEIGHTS_PATH constant**

Immediately after `ANNOTATION_FPS`:

```python
# Path to the L2CS-Net gaze model weights file.
GAZE_WEIGHTS_PATH = ROOT / "models" / "L2CSNet_gaze360.pkl"
```

- [ ] **Step 3: Verify**

```bash
source venv/bin/activate
python -c "from config.config import ANNOTATION_FPS, GAZE_WEIGHTS_PATH; print(ANNOTATION_FPS, GAZE_WEIGHTS_PATH)"
```

Expected: `2.0 /home/anirban/asd_video_analyzer/models/L2CSNet_gaze360.pkl`

- [ ] **Step 4: Commit**

```bash
git add config/config.py
git commit -m "feat: add ANNOTATION_FPS and GAZE_WEIGHTS_PATH config constants"
```

---

### Task 3: Create annotator.py skeleton with pure helper functions

**Files:**
- Create: `src/annotator.py`
- Create: `tests/__init__.py`
- Create: `tests/test_annotator.py`

- [ ] **Step 1: Create tests directory**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 2: Write failing tests for pure helper functions**

Create `tests/test_annotator.py`:

```python
"""Unit tests for pure (model-free) helper functions in src/annotator.py."""
import pytest


# ---------------------------------------------------------------------------
# _is_linear
# ---------------------------------------------------------------------------

def test_is_linear_collinear_horizontal():
    from src.annotator import _is_linear
    centers = [(0.1, 0.5), (0.3, 0.5), (0.5, 0.5), (0.7, 0.5)]
    assert _is_linear(centers) is True


def test_is_linear_collinear_diagonal():
    from src.annotator import _is_linear
    centers = [(0.1, 0.1), (0.3, 0.3), (0.5, 0.5)]
    assert _is_linear(centers) is True


def test_is_linear_scattered():
    from src.annotator import _is_linear
    centers = [(0.1, 0.1), (0.9, 0.2), (0.3, 0.8)]
    assert _is_linear(centers) is False


def test_is_linear_too_few_objects():
    from src.annotator import _is_linear
    assert _is_linear([(0.1, 0.1), (0.5, 0.5)]) is False


# ---------------------------------------------------------------------------
# _window_words
# ---------------------------------------------------------------------------

def test_window_words_returns_words_in_range():
    from src.annotator import _window_words
    words = [
        {"word": "hello", "start": 1.0, "end": 1.5},
        {"word": "world", "start": 5.0, "end": 5.5},
        {"word": "bye",   "start": 15.0, "end": 15.5},
    ]
    result = _window_words(words, t_center=5.0, window=3.0)
    assert len(result) == 2
    assert result[0]["word"] == "hello"
    assert result[1]["word"] == "world"


def test_window_words_empty_when_no_speech():
    from src.annotator import _window_words
    words = [{"word": "hi", "start": 30.0, "end": 30.5}]
    result = _window_words(words, t_center=5.0, window=3.0)
    assert result == []


# ---------------------------------------------------------------------------
# _detect_echolalia
# ---------------------------------------------------------------------------

def test_detect_echolalia_finds_repetition():
    from src.annotator import _detect_echolalia
    words = [{"word": w} for w in ["go", "go", "go", "go"]]
    result = _detect_echolalia(words)
    assert result is not None
    assert "go" in result
    assert "4" in result


def test_detect_echolalia_ignores_stopwords():
    from src.annotator import _detect_echolalia
    words = [{"word": w} for w in ["the", "the", "the", "ball"]]
    result = _detect_echolalia(words)
    assert result is None


def test_detect_echolalia_none_when_no_repetition():
    from src.annotator import _detect_echolalia
    words = [{"word": w} for w in ["i", "want", "the", "ball"]]
    assert _detect_echolalia(words) is None


# ---------------------------------------------------------------------------
# _detect_pronoun_reversal
# ---------------------------------------------------------------------------

def test_detect_pronoun_reversal_found():
    from src.annotator import _detect_pronoun_reversal
    words = [{"word": w} for w in ["you", "want", "juice"]]
    assert _detect_pronoun_reversal(words) is True


def test_detect_pronoun_reversal_not_found():
    from src.annotator import _detect_pronoun_reversal
    words = [{"word": w} for w in ["i", "want", "juice"]]
    assert _detect_pronoun_reversal(words) is False


# ---------------------------------------------------------------------------
# _gaze_to_description
# ---------------------------------------------------------------------------

def test_gaze_to_description_left():
    from src.annotator import _gaze_to_description
    desc = _gaze_to_description(pitch_deg=5.0, yaw_deg=-35.0)
    assert "left" in desc.lower()
    assert "35" in desc


def test_gaze_to_description_camera():
    from src.annotator import _gaze_to_description
    desc = _gaze_to_description(pitch_deg=2.0, yaw_deg=3.0)
    assert "camera" in desc.lower()


def test_gaze_to_description_down():
    from src.annotator import _gaze_to_description
    desc = _gaze_to_description(pitch_deg=-25.0, yaw_deg=0.0)
    assert "down" in desc.lower()
```

- [ ] **Step 3: Run tests — confirm they all fail**

```bash
source venv/bin/activate
pytest tests/test_annotator.py -v 2>&1 | head -40
```

Expected: all tests fail with `ImportError: cannot import name '_is_linear' from 'src.annotator'` (module doesn't exist yet).

- [ ] **Step 4: Create src/annotator.py with pure helper functions only**

Create `src/annotator.py`:

```python
"""Specialized model annotation layer for ASD signal detection.

Runs L2CS-Net (gaze), MediaPipe Pose+Hands (motor), YOLOv8m (objects),
and frame-aligned Whisper NLP (language) on extracted thumbnails.
Results are stored as natural language strings keyed by thumbnail filename.

Public API:
    annotate_frames(thumb_paths, transcript_json, fps) -> dict[str, dict[str, str]]
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Lazy model globals — loaded on first call, held for the session lifetime
# ---------------------------------------------------------------------------
_gaze_pipeline = None
_pose_model = None
_hands_model = None
_yolo_model = None


def _get_device():
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


# ---------------------------------------------------------------------------
# Pure helper functions (model-free, fully testable)
# ---------------------------------------------------------------------------

def _is_linear(centers: list[tuple[float, float]], threshold: float = 0.15) -> bool:
    """Return True if 3+ points are approximately collinear.

    Uses the ratio of the smallest singular value to the largest to detect
    collinearity. All coordinates should be in [0, 1] (normalized).
    """
    if len(centers) < 3:
        return False
    pts = np.array(centers, dtype=float)
    pts -= pts.mean(axis=0)
    _, s, _ = np.linalg.svd(pts)
    if s[0] < 1e-9:
        return False
    return float(s[1] / s[0]) < threshold


def _window_words(
    all_words: list[dict],
    t_center: float,
    window: float = 3.0,
) -> list[dict]:
    """Return words whose midpoint falls within [t_center - window, t_center + window]."""
    lo = t_center - window
    hi = t_center + window
    return [
        w for w in all_words
        if lo <= (w.get("start", 0) + w.get("end", 0)) / 2 <= hi
    ]


_STOPWORDS = frozenset({
    "the", "a", "an", "is", "it", "i", "you", "and", "to", "in",
    "of", "that", "was", "he", "she", "they", "we", "are", "be",
    "at", "or", "but", "not", "with", "on", "do", "did",
})


def _detect_echolalia(words: list[dict]) -> Optional[str]:
    """Return a description string if echolalia is detected, else None.

    Echolalia: any non-stopword repeated 3+ times in the window.
    """
    texts = [w["word"].strip().lower().rstrip(".,!?") for w in words]
    counts = Counter(t for t in texts if t and t not in _STOPWORDS and len(t) > 1)
    for word, count in counts.most_common():
        if count >= 3:
            return f"'{word}' repeated {count} times — possible echolalia"
    return None


_PRONOUN_REVERSAL_PAIRS = {
    "you": {"want", "need", "like", "have", "don't", "do", "going", "eat", "drink"},
}


def _detect_pronoun_reversal(words: list[dict]) -> bool:
    """Return True if a pronoun-reversal pattern is detected.

    Looks for 'you + verb' patterns that suggest the subject is using 'you'
    to refer to themselves (e.g. 'you want juice' meaning 'I want juice').
    """
    texts = [w["word"].strip().lower().rstrip(".,!?") for w in words]
    for i, token in enumerate(texts[:-1]):
        if token in _PRONOUN_REVERSAL_PAIRS:
            if texts[i + 1] in _PRONOUN_REVERSAL_PAIRS[token]:
                return True
    return False


def _gaze_to_description(pitch_deg: float, yaw_deg: float) -> str:
    """Convert L2CS-Net gaze angles (degrees) to a natural language string.

    Convention: yaw < 0 → looking left, yaw > 0 → looking right.
    pitch < 0 → looking down, pitch > 0 → looking up.
    """
    parts = []
    if abs(yaw_deg) <= 10 and abs(pitch_deg) <= 10:
        return "Gaze directed toward camera centre. Possible eye contact."
    if yaw_deg < -10:
        parts.append(f"Gaze directed {abs(yaw_deg):.0f}° left of camera")
    elif yaw_deg > 10:
        parts.append(f"Gaze directed {yaw_deg:.0f}° right of camera")
    if pitch_deg < -10:
        parts.append(f"{abs(pitch_deg):.0f}° downward")
    elif pitch_deg > 10:
        parts.append(f"{pitch_deg:.0f}° upward")
    return ", ".join(parts) + ". No visible social target in frame." if parts else "Gaze direction indeterminate."


def _thumb_timestamp(thumb_path: Path, fps: float) -> float:
    """Derive video timestamp (seconds) from thumbnail filename and fps."""
    m = re.search(r"(\d+)", thumb_path.stem)
    if not m:
        return 0.0
    return (int(m.group(1)) - 1) / fps
```

- [ ] **Step 5: Run tests — confirm pure-function tests pass**

```bash
source venv/bin/activate
pytest tests/test_annotator.py -v 2>&1 | head -50
```

Expected: all tests pass (green).

- [ ] **Step 6: Commit**

```bash
git add src/annotator.py tests/__init__.py tests/test_annotator.py
git commit -m "feat: add annotator skeleton with pure helper functions and tests"
```

---

### Task 4: Implement gaze annotation (L2CS-Net, Signal 1)

**Files:**
- Modify: `src/annotator.py`

- [ ] **Step 1: Add gaze model loader and inference function**

Append to `src/annotator.py` (after `_thumb_timestamp`):

```python
# ---------------------------------------------------------------------------
# Gaze annotation — Signal 1 (L2CS-Net)
# ---------------------------------------------------------------------------

def _load_gaze_pipeline():
    global _gaze_pipeline
    if _gaze_pipeline is not None:
        return _gaze_pipeline
    import torch
    from l2cs import Pipeline
    from config.config import GAZE_WEIGHTS_PATH

    if not GAZE_WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"L2CS-Net weights not found at {GAZE_WEIGHTS_PATH}. "
            "Run Task 1 Step 2 of the implementation plan to download them."
        )
    device = torch.device(_get_device())
    _gaze_pipeline = Pipeline(
        weights=GAZE_WEIGHTS_PATH,
        arch="ResNet50",
        device=device,
        include_detector=True,
        confidence_threshold=0.5,
    )
    return _gaze_pipeline


def _annotate_gaze(frame_bgr: np.ndarray) -> str:
    """Run L2CS-Net on a BGR frame and return a natural language gaze string."""
    try:
        pipeline = _load_gaze_pipeline()
        import torch
        with torch.no_grad():
            results = pipeline.step(frame_bgr)
        if results is None or len(results.pitch) == 0:
            return "Face not detected — gaze unassessable."
        pitch_deg = float(np.degrees(results.pitch[0]))
        yaw_deg = float(np.degrees(results.yaw[0]))
        return _gaze_to_description(pitch_deg, yaw_deg)
    except FileNotFoundError as e:
        return f"Gaze model unavailable: {e}"
    except Exception as e:
        return f"Gaze unassessable (inference error: {type(e).__name__})."
```

- [ ] **Step 2: Smoke-test gaze annotation on a real thumbnail**

```bash
source venv/bin/activate
python -c "
import cv2, pathlib, sys
# Use any existing thumbnail; substitute a real path if needed
thumbs = sorted(pathlib.Path('processed').glob('*/thumbs/thumb_*.jpg'))
if not thumbs:
    print('No thumbnails found — process a video first')
    sys.exit(0)
frame = cv2.imread(str(thumbs[0]))
from src.annotator import _annotate_gaze
print(_annotate_gaze(frame))
"
```

Expected: a natural language gaze string like `"Gaze directed 28° left of camera. No visible social target in frame."` or `"Face not detected — gaze unassessable."`. No exception.

- [ ] **Step 3: Commit**

```bash
git add src/annotator.py
git commit -m "feat: add L2CS-Net gaze annotation for signal 1"
```

---

### Task 5: Implement pose annotation (MediaPipe Pose + Hands, Signals 7/8/9)

**Files:**
- Modify: `src/annotator.py`

- [ ] **Step 1: Add pose model loader and geometry helpers**

Append to `src/annotator.py`:

```python
# ---------------------------------------------------------------------------
# Pose annotation — Signals 7, 8, 9 (MediaPipe Pose + Hands)
# ---------------------------------------------------------------------------

# MediaPipe landmark indices
_MP_LEFT_SHOULDER  = 11
_MP_RIGHT_SHOULDER = 12
_MP_LEFT_ELBOW     = 13
_MP_RIGHT_ELBOW    = 14
_MP_LEFT_WRIST     = 15
_MP_RIGHT_WRIST    = 16
_MP_LEFT_HIP       = 23
_MP_RIGHT_HIP      = 24


def _load_pose_model():
    global _pose_model
    if _pose_model is not None:
        return _pose_model
    import mediapipe as mp
    _pose_model = mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        enable_segmentation=False,
        min_detection_confidence=0.5,
    )
    return _pose_model


def _load_hands_model():
    global _hands_model
    if _hands_model is not None:
        return _hands_model
    import mediapipe as mp
    _hands_model = mp.solutions.hands.Hands(
        static_image_mode=True,
        max_num_hands=2,
        min_detection_confidence=0.5,
    )
    return _hands_model


def _annotate_pose(frame_bgr: np.ndarray) -> str:
    """Return a natural language posture description from MediaPipe landmarks."""
    try:
        import mediapipe as mp
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        pose = _load_pose_model()
        pose_results = pose.process(rgb)

        hands = _load_hands_model()
        hands_results = hands.process(rgb)

        if pose_results.pose_landmarks is None:
            return "Pose not detected — body not visible in frame."

        lm = pose_results.pose_landmarks.landmark

        l_shoulder = lm[_MP_LEFT_SHOULDER]
        r_shoulder = lm[_MP_RIGHT_SHOULDER]
        l_wrist    = lm[_MP_LEFT_WRIST]
        r_wrist    = lm[_MP_RIGHT_WRIST]
        l_elbow    = lm[_MP_LEFT_ELBOW]
        r_elbow    = lm[_MP_RIGHT_ELBOW]
        l_hip      = lm[_MP_LEFT_HIP]
        r_hip      = lm[_MP_RIGHT_HIP]

        observations = []

        # --- Signal 9: wrist elevation (flapping posture) ---
        left_elevated  = l_wrist.y < l_shoulder.y   # y axis: smaller = higher in frame
        right_elevated = r_wrist.y < r_shoulder.y
        if left_elevated and right_elevated:
            observations.append(
                "Both wrists elevated above shoulders with arms extended laterally — "
                "consistent with mid-flap posture (signal 9)."
            )
        elif left_elevated or right_elevated:
            side = "Left" if left_elevated else "Right"
            observations.append(
                f"{side} wrist elevated above shoulder — partial flap posture possible (signal 9)."
            )

        # --- Signal 8: rotational stance ---
        shoulder_width = abs(l_shoulder.x - r_shoulder.x)
        hip_width      = abs(l_hip.x - r_hip.x)
        # Arms outstretched + body axis twist: shoulder width significantly > hip width
        l_arm_extended = abs(l_wrist.x - l_shoulder.x) > shoulder_width * 0.8
        r_arm_extended = abs(r_wrist.x - r_shoulder.x) > shoulder_width * 0.8
        if l_arm_extended and r_arm_extended and shoulder_width > hip_width * 1.2:
            observations.append(
                "Body rotational stance: arms outstretched, shoulder span exceeds hip width — "
                "consistent with mid-spin posture (signal 8)."
            )

        # --- Signal 7: hand-to-body contact ---
        hand_obs = []
        if hands_results.multi_hand_landmarks:
            for hand_lm in hands_results.multi_hand_landmarks:
                # Wrist landmark of detected hand
                hw = hand_lm.landmark[0]
                # Check proximity to torso (between shoulders and hips)
                torso_x_lo = min(l_shoulder.x, r_shoulder.x)
                torso_x_hi = max(l_shoulder.x, r_shoulder.x)
                torso_y_lo = min(l_shoulder.y, r_shoulder.y)
                torso_y_hi = max(l_hip.y, r_hip.y)
                in_torso_x = torso_x_lo - 0.1 <= hw.x <= torso_x_hi + 0.1
                in_torso_y = torso_y_lo - 0.1 <= hw.y <= torso_y_hi + 0.1
                if in_torso_x and in_torso_y:
                    hand_obs.append("hand in contact with torso region")
                # Check proximity to head (above shoulders)
                if hw.y < min(l_shoulder.y, r_shoulder.y) - 0.05:
                    hand_obs.append("hand elevated near head region")

        if hand_obs:
            observations.append(
                f"Self-contact posture: {'; '.join(hand_obs)} — "
                "possible self-hitting evidence (signal 7)."
            )

        if not observations:
            return "Pose detected. No atypical posture patterns identified."
        return " ".join(observations)

    except Exception as e:
        return f"Pose unassessable (error: {type(e).__name__})."
```

- [ ] **Step 2: Smoke-test pose annotation**

```bash
source venv/bin/activate
python -c "
import cv2, pathlib, sys
thumbs = sorted(pathlib.Path('processed').glob('*/thumbs/thumb_*.jpg'))
if not thumbs:
    print('No thumbnails — process a video first'); sys.exit(0)
frame = cv2.imread(str(thumbs[0]))
from src.annotator import _annotate_pose
print(_annotate_pose(frame))
"
```

Expected: a string describing posture or `"Pose not detected — body not visible in frame."`. No exception.

- [ ] **Step 3: Commit**

```bash
git add src/annotator.py
git commit -m "feat: add MediaPipe pose+hands annotation for signals 7/8/9"
```

---

### Task 6: Implement object annotation (YOLOv8m, Signal 6)

**Files:**
- Modify: `src/annotator.py`

- [ ] **Step 1: Add YOLO model loader and object detection function**

Append to `src/annotator.py`:

```python
# ---------------------------------------------------------------------------
# Object annotation — Signal 6 (YOLOv8m)
# ---------------------------------------------------------------------------

def _load_yolo_model():
    global _yolo_model
    if _yolo_model is not None:
        return _yolo_model
    from ultralytics import YOLO
    _yolo_model = YOLO("yolov8m.pt")   # downloads weights on first call (~50 MB)
    return _yolo_model


def _annotate_objects(frame_bgr: np.ndarray) -> str:
    """Run YOLOv8m and return a natural language object arrangement description."""
    try:
        model = _load_yolo_model()
        results = model(frame_bgr, verbose=False)
        boxes = results[0].boxes

        if boxes is None or len(boxes) == 0:
            return "No objects detected in frame."

        cls_ids = boxes.cls.cpu().numpy().astype(int)
        xyxy    = boxes.xyxy.cpu().numpy()
        names   = model.names

        # Group by class name
        class_groups: dict[str, list[tuple[float, float]]] = {}
        for cls_id, box in zip(cls_ids, xyxy):
            label = names[cls_id]
            cx = float((box[0] + box[2]) / 2) / frame_bgr.shape[1]   # normalize
            cy = float((box[1] + box[3]) / 2) / frame_bgr.shape[0]
            class_groups.setdefault(label, []).append((cx, cy))

        observations = []
        for label, centers in class_groups.items():
            if len(centers) >= 3 and _is_linear(centers):
                observations.append(
                    f"{len(centers)} objects of class '{label}' in a linear arrangement — "
                    "consistent with object lining-up (signal 6)."
                )

        # Flag round/spinning objects (balls, wheels, tops)
        spinning_classes = {"sports ball", "frisbee", "clock", "donut"}
        for label in class_groups:
            if label in spinning_classes:
                observations.append(
                    f"Round object detected: '{label}' — may be relevant to spinning behavior (signal 8)."
                )

        if not observations:
            return "No linear or symmetric object arrangement detected."
        return " ".join(observations)

    except Exception as e:
        return f"Object detection unavailable (error: {type(e).__name__})."
```

- [ ] **Step 2: Smoke-test object annotation**

```bash
source venv/bin/activate
python -c "
import cv2, pathlib, sys
thumbs = sorted(pathlib.Path('processed').glob('*/thumbs/thumb_*.jpg'))
if not thumbs:
    print('No thumbnails — process a video first'); sys.exit(0)
frame = cv2.imread(str(thumbs[0]))
from src.annotator import _annotate_objects
print(_annotate_objects(frame))
"
```

Expected: `"No linear or symmetric object arrangement detected."` or a description of detected objects. First run downloads `yolov8m.pt` (~50 MB).

- [ ] **Step 3: Commit**

```bash
git add src/annotator.py
git commit -m "feat: add YOLOv8m object arrangement annotation for signal 6"
```

---

### Task 7: Implement language annotation (Whisper word timestamps + NLP, Signals 4/5)

**Files:**
- Modify: `src/annotator.py`

- [ ] **Step 1: Add language annotation function**

Append to `src/annotator.py`:

```python
# ---------------------------------------------------------------------------
# Language annotation — Signals 4, 5 (Whisper word timestamps + NLP)
# ---------------------------------------------------------------------------

def _load_words_json(words_json_path: Path) -> list[dict]:
    """Load and flatten all words from a Whisper word-timestamp JSON file."""
    try:
        data = json.loads(words_json_path.read_text(encoding="utf-8"))
        all_words: list[dict] = []
        for segment in data.get("segments", []):
            all_words.extend(segment.get("words", []))
        return all_words
    except Exception:
        return []


def _annotate_language(
    thumb_path: Path,
    all_words: list[dict],
    fps: float,
) -> str:
    """Return a natural language string describing speech near this frame.

    Uses a ±3 second window around the frame's video timestamp.
    """
    t_center = _thumb_timestamp(thumb_path, fps)
    window_words = _window_words(all_words, t_center, window=3.0)

    if not window_words:
        return f"t={t_center:.0f}s window: no speech detected near this frame."

    # Build readable transcript snippet
    snippet = " ".join(w["word"] for w in window_words).strip()
    observations = [f"t={t_center:.0f}s window: speech — \"{snippet[:80]}\""]

    echolalia = _detect_echolalia(window_words)
    if echolalia:
        observations.append(echolalia)

    if _detect_pronoun_reversal(window_words):
        observations.append("pronoun reversal candidate ('you' used in first-person context).")

    return " ".join(observations)
```

- [ ] **Step 2: Run language-annotation tests**

```bash
source venv/bin/activate
pytest tests/test_annotator.py -v -k "echolalia or pronoun or window"
```

Expected: all matching tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/annotator.py
git commit -m "feat: add frame-aligned language annotation for signals 4/5"
```

---

### Task 8: Implement annotate_frames() public orchestrator

**Files:**
- Modify: `src/annotator.py`

- [ ] **Step 1: Add the public annotate_frames() function**

Append to `src/annotator.py`:

```python
# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def annotate_frames(
    thumb_paths: list[Path],
    transcript_json: Optional[Path],
    fps: float,
) -> dict[str, dict[str, str]]:
    """Annotate a list of thumbnail frames with all specialized models.

    Parameters
    ----------
    thumb_paths:
        Ordered list of thumbnail Paths (e.g. thumb_00001.jpg …).
    transcript_json:
        Path to a Whisper word-timestamp JSON file (.words.json), or None.
    fps:
        Thumbnail extraction fps (used to derive frame timestamps).

    Returns
    -------
    dict keyed by thumbnail basename (e.g. "thumb_00001.jpg"), with sub-dict:
        {"gaze": str, "pose": str, "objects": str, "language": str}
    """
    from config.config import ANNOTATION_FPS

    stride = max(1, round(fps / ANNOTATION_FPS))
    all_words = _load_words_json(transcript_json) if transcript_json else []
    annotations: dict[str, dict[str, str]] = {}

    for i, thumb in enumerate(thumb_paths):
        if i % stride != 0:
            continue
        frame_bgr = cv2.imread(str(thumb))
        if frame_bgr is None:
            continue
        annotations[thumb.name] = {
            "gaze":     _annotate_gaze(frame_bgr),
            "pose":     _annotate_pose(frame_bgr),
            "objects":  _annotate_objects(frame_bgr),
            "language": _annotate_language(thumb, all_words, fps),
        }

    return annotations
```

- [ ] **Step 2: Smoke-test the full annotate_frames() call**

```bash
source venv/bin/activate
python -c "
import pathlib, json, sys
thumbs = sorted(pathlib.Path('processed').glob('*/thumbs/thumb_*.jpg'))[:3]
if not thumbs:
    print('No thumbnails — process a video first'); sys.exit(0)
from src.annotator import annotate_frames
result = annotate_frames(thumbs, transcript_json=None, fps=2.0)
print(json.dumps(result, indent=2))
"
```

Expected: JSON output with 3 entries (or fewer if stride > 1), each with gaze/pose/objects/language keys. No exception.

- [ ] **Step 3: Commit**

```bash
git add src/annotator.py
git commit -m "feat: add annotate_frames() public orchestrator"
```

---

### Task 9: Add transcribe_mp3_with_timestamps() to processor.py

**Files:**
- Modify: `src/processor.py`

- [ ] **Step 1: Add transcribe_mp3_with_timestamps() after transcribe_mp3()**

In `src/processor.py`, after the `transcribe_mp3()` function (around line 196), add:

```python
def transcribe_mp3_with_timestamps(mp3_path: Path, output_dir: Path) -> Optional[Path]:
    """Transcribe mp3 using Whisper with word-level timestamps.

    Saves a JSON file alongside the .txt transcript containing all segments
    and per-word start/end times. Returns the Path to the JSON file, or None
    on failure.

    The JSON structure matches Whisper's native output:
        {"segments": [{"start": float, "end": float, "text": str,
                        "words": [{"word": str, "start": float, "end": float}, ...]}, ...]}
    """
    import json as _json

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / (mp3_path.stem + ".words.json")

    try:
        import whisper as _whisper
        device = "cuda" if _cuda_available() else "cpu"
        model = _whisper.load_model(
            "base", device=device,
            download_root=u_utils.WHISPER_CACHE_DIR,
        )
        result = model.transcribe(str(mp3_path), word_timestamps=True)
        # Keep only the fields we need to keep the file small
        segments_out = []
        for seg in result.get("segments", []):
            segments_out.append({
                "start": seg["start"],
                "end":   seg["end"],
                "text":  seg["text"],
                "words": [
                    {"word": w["word"], "start": w["start"], "end": w["end"]}
                    for w in seg.get("words", [])
                ],
            })
        json_path.write_text(
            _json.dumps({"segments": segments_out}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return json_path
    except Exception as e:
        print(f"[whisper word timestamps] {e}")
        return None
```

- [ ] **Step 2: Verify the function is importable**

```bash
source venv/bin/activate
python -c "from src.processor import transcribe_mp3_with_timestamps; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/processor.py
git commit -m "feat: add transcribe_mp3_with_timestamps() for word-level alignment"
```

---

### Task 10: Update process_video() to call the annotator

**Files:**
- Modify: `src/processor.py`

- [ ] **Step 1: Add json import at the top of processor.py**

In `src/processor.py`, add `import json` to the existing imports block (after the `import hashlib` line).

- [ ] **Step 2: Replace process_video() with the updated version**

Find the `process_video()` function in `src/processor.py` (starts around line 198). Replace the entire function body with:

```python
def process_video(video_path: Path, force: bool = False) -> None:
    """Perform the full pipeline for a single upload.

    * create processed/<basename>/ and thumbs/ subdirectory
    * convert video -> mp3
    * extract thumbnails at 2 fps
    * run whisper to transcribe audio with word timestamps
    * run specialized model annotation on thumbnails

    If ``force`` is False the full pipeline is skipped when already processed,
    but annotation is still run if annotations.json is missing.
    """
    from config.config import ANNOTATION_FPS
    from src.annotator import annotate_frames

    ensure_dirs()
    target = get_processed_folder(video_path.name)
    thumbs = target / "thumbs"
    transcript_path = target / (video_path.stem + ".txt")
    words_json_path = target / (video_path.stem + ".words.json")
    annotations_path = thumbs / "annotations.json"

    already_processed = target.exists() and transcript_path.is_file()

    if already_processed and not force:
        # Full pipeline already done — only annotate if missing (new feature)
        if not annotations_path.exists():
            thumb_list = sorted(thumbs.glob("thumb_*.jpg"))
            result = annotate_frames(
                thumb_list,
                words_json_path if words_json_path.exists() else None,
                fps=2.0,
            )
            annotations_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return

    target.mkdir(parents=True, exist_ok=True)
    thumbs.mkdir(parents=True, exist_ok=True)

    mp3_out = target / (video_path.stem + ".mp3")
    convert_to_mp3(video_path, mp3_out)
    generate_thumbnails(video_path, thumbs)

    # Transcription — best-effort; word timestamps preferred
    if not transcribe_mp3_with_timestamps(mp3_out, target):
        transcribe_mp3(mp3_out, target)   # fall back to plain .txt only

    # Annotation — run after thumbnails and transcript are ready
    thumb_list = sorted(thumbs.glob("thumb_*.jpg"))
    result = annotate_frames(
        thumb_list,
        words_json_path if words_json_path.exists() else None,
        fps=2.0,
    )
    annotations_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
```

- [ ] **Step 3: Verify process_video() is importable**

```bash
source venv/bin/activate
python -c "from src.processor import process_video; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: End-to-end pipeline test on a short video**

If a video is already in `uploads/`:

```bash
source venv/bin/activate
python -c "
import pathlib
from src.processor import process_video
videos = list(pathlib.Path('uploads').glob('*.mp4'))
if not videos:
    print('No videos in uploads/ — upload one via the UI first')
else:
    process_video(videos[0], force=True)
    stem = videos[0].stem
    ann = pathlib.Path(f'processed/{stem}/thumbs/annotations.json')
    print('annotations.json exists:', ann.exists())
    import json
    data = json.loads(ann.read_text())
    first_key = next(iter(data))
    print(first_key, '->', list(data[first_key].keys()))
"
```

Expected output:
```
annotations.json exists: True
thumb_00001.jpg -> ['gaze', 'pose', 'objects', 'language']
```

- [ ] **Step 5: Commit**

```bash
git add src/processor.py
git commit -m "feat: integrate annotate_frames() into process_video() pipeline"
```

---

### Task 11: Update analyzer.py to inject FRAME_ANNOTATIONS

**Files:**
- Modify: `src/analyzer.py`

- [ ] **Step 1: Add json import to analyzer.py**

In `src/analyzer.py`, add `import json` to the existing imports block (after `import base64`).

- [ ] **Step 2: Add _build_frame_annotations_block() helper**

In `src/analyzer.py`, after the `_encode_images()` function, add:

```python
def _build_frame_annotations_block(
    selected_thumb_paths: list[Path],
    annotations: dict,
) -> str:
    """Build the FRAME_ANNOTATIONS: prompt block from cached annotation data.

    Returns an empty string if no annotations are available.
    """
    if not annotations or not selected_thumb_paths:
        return ""

    lines = [
        "",
        "FRAME_ANNOTATIONS:",
        "(Pre-computed measurements from specialized vision and language models.",
        "These complement your own visual analysis. For quantitative claims —",
        "gaze angle, object count, transcript content, posture geometry — weight",
        "these annotations more heavily than visual estimation alone.",
        "If an annotation states a condition is unassessable, factor that into",
        "your confidence and mark Unclear if no other evidence supports Yes.)",
        "",
    ]

    for i, thumb in enumerate(selected_thumb_paths, 1):
        ann = annotations.get(thumb.name, {})
        if not ann:
            continue
        lines.append(f"Frame_{i}:")
        for key in ("gaze", "pose", "objects", "language"):
            if key in ann:
                lines.append(f"  {key}: {ann[key]}")
        lines.append("")

    return "\n".join(lines)


def _load_annotations(selected_thumb_paths: list[Path]) -> dict:
    """Load annotations.json for the video containing the selected thumbnails."""
    if not selected_thumb_paths:
        return {}
    annotations_path = selected_thumb_paths[0].parent / "annotations.json"
    if not annotations_path.exists():
        return {}
    try:
        return json.loads(annotations_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
```

- [ ] **Step 3: Update analyze() to inject annotations**

In `src/analyzer.py`, find the `analyze()` function. Replace the lines that build `prompt`:

```python
    # Use ASD default prompt if no custom prompt provided
    prompt = user_prompt or DEFAULT_ASD_PROMPT

    # combine with transcript if available
    if transcript:
        prompt = f"{prompt}\n\nTranscript context:\n{transcript}"
```

with:

```python
    # Use ASD default prompt if no custom prompt provided
    prompt = user_prompt or DEFAULT_ASD_PROMPT

    # combine with transcript if available
    if transcript:
        prompt = f"{prompt}\n\nTranscript context:\n{transcript}"

    # Inject FRAME_ANNOTATIONS from cached specialized model output
    annotations = _load_annotations(selected_thumb_paths or [])
    fa_block = _build_frame_annotations_block(selected_thumb_paths or [], annotations)
    if fa_block:
        prompt = prompt + fa_block
```

- [ ] **Step 4: Apply the same change to analyze_stream()**

In `src/analyzer.py`, find `analyze_stream()`. Apply the identical injection after the transcript block:

```python
    # Use ASD default prompt if no custom prompt provided
    prompt = user_prompt or DEFAULT_ASD_PROMPT
    if transcript:
        prompt = f"{prompt}\n\nTranscript context:\n{transcript}"

    # Inject FRAME_ANNOTATIONS from cached specialized model output
    annotations = _load_annotations(selected_thumb_paths or [])
    fa_block = _build_frame_annotations_block(selected_thumb_paths or [], annotations)
    if fa_block:
        prompt = prompt + fa_block
```

- [ ] **Step 5: Verify the module imports cleanly**

```bash
source venv/bin/activate
python -c "from src.analyzer import analyze, analyze_stream, _load_annotations, _build_frame_annotations_block; print('OK')"
```

Expected: `OK`

- [ ] **Step 6: Verify the annotations block is built correctly**

```bash
source venv/bin/activate
python -c "
import pathlib, json
from src.analyzer import _load_annotations, _build_frame_annotations_block

# Find any annotated thumbnails
thumbs = sorted(pathlib.Path('processed').glob('*/thumbs/thumb_*.jpg'))[:2]
if not thumbs:
    print('No annotated thumbnails yet — run process_video() first')
else:
    annotations = _load_annotations(thumbs)
    block = _build_frame_annotations_block(thumbs, annotations)
    print(block[:600])
"
```

Expected: prints a `FRAME_ANNOTATIONS:` block with gaze/pose/objects/language entries for each frame.

- [ ] **Step 7: Commit**

```bash
git add src/analyzer.py
git commit -m "feat: inject FRAME_ANNOTATIONS block into VLM prompt from annotations.json"
```

---

### Task 12: Update DEFAULT_ASD_PROMPT with FRAME_ANNOTATIONS instructions

**Files:**
- Modify: `config/config.py`

- [ ] **Step 1: Add FRAME_ANNOTATIONS usage instructions to DEFAULT_ASD_PROMPT**

In `config/config.py`, find `DEFAULT_ASD_PROMPT`. Locate this line near the top of the prompt (after the opening `"""You are a behavioral analyst...`):

```
Signal Numbers (used below):
```

Insert the following block immediately before `Signal Numbers (used below):`:

```
When a FRAME_ANNOTATIONS section appears below, treat it as objective measurements
from specialized vision and language models that ran before this analysis. These
complement — not replace — your visual interpretation of the frames. For quantitative
claims (gaze angle in degrees, object arrangement, posture geometry, transcript
content), weight the annotations more heavily than your own visual estimate. If an
annotation says a condition is unassessable, mark that signal Unclear unless you have
strong contradicting visual evidence.

Signals 2 (Aggressive Behavior) and 3 (Hyper-/Hyporeactivity to Sensory Input) are
assessed from your visual analysis only — no annotation is provided for them.

```

- [ ] **Step 2: Verify the prompt still loads correctly**

```bash
source venv/bin/activate
python -c "
from config.config import DEFAULT_ASD_PROMPT
assert 'FRAME_ANNOTATIONS' in DEFAULT_ASD_PROMPT
assert 'Signal Numbers' in DEFAULT_ASD_PROMPT
print('Prompt length:', len(DEFAULT_ASD_PROMPT))
print('FRAME_ANNOTATIONS instruction present: OK')
"
```

Expected: `FRAME_ANNOTATIONS instruction present: OK` with a non-zero prompt length.

- [ ] **Step 3: Commit**

```bash
git add config/config.py
git commit -m "feat: add FRAME_ANNOTATIONS usage instructions to DEFAULT_ASD_PROMPT"
```

---

### Task 13: Run all tests and manual end-to-end verification

**Files:** None (read-only verification)

- [ ] **Step 1: Run full test suite**

```bash
source venv/bin/activate
pytest tests/ -v
```

Expected: all tests pass. Note any failures and fix before proceeding.

- [ ] **Step 2: Start the app**

```bash
source venv/bin/activate
streamlit run app.py
```

- [ ] **Step 3: Process a video with visible ASD behaviors**

Upload or select a video where ASD behaviors are clearly present (e.g., arm flapping, gaze aversion, object arrangement). Click **Process**. Wait for the full pipeline including annotation to complete. Confirm in the terminal that no errors appear.

- [ ] **Step 4: Verify annotations.json was created**

```bash
ls -lh processed/*/thumbs/annotations.json
```

Expected: file exists with non-zero size.

- [ ] **Step 5: Inspect annotation quality for a few frames**

```bash
source venv/bin/activate
python -c "
import json, pathlib
for p in pathlib.Path('processed').glob('*/thumbs/annotations.json'):
    data = json.loads(p.read_text())
    for fname, ann in list(data.items())[:3]:
        print(f'\n--- {fname} ---')
        for k, v in ann.items():
            print(f'  {k}: {v}')
"
```

Expected: gaze strings include angles (not just "unassessable"), pose strings describe body position, object strings describe detected objects.

- [ ] **Step 6: Run analysis and confirm FRAME_ANNOTATIONS in prompt**

Select 3–5 frames and click **Run Analysis**. In the terminal output (Streamlit logs), confirm the request payload contains `FRAME_ANNOTATIONS:`. Check that:
- At least one signal (1–9) reports `Yes` for frames showing the behavior
- The CLINICAL NARRATIVE references annotation evidence (e.g., mentions gaze angle, posture)

- [ ] **Step 7: Verify idempotency**

Run `process_video()` a second time on the same video without `force=True`. Confirm `annotations.json` is not rewritten (check file modification time).

```bash
stat processed/*/thumbs/annotations.json | grep Modify
# wait 2 seconds, then re-process
source venv/bin/activate
python -c "
import pathlib
from src.processor import process_video
v = next(pathlib.Path('uploads').glob('*.mp4'))
process_video(v)
print('Done')
"
stat processed/*/thumbs/annotations.json | grep Modify
```

Expected: the `Modify` timestamp does not change.

- [ ] **Step 8: Check app.py calls process_video() — add spinner if not already present**

Open `app.py` and find where `process_video()` is called. If it is not already wrapped in a spinner, wrap it:

```python
with st.spinner("Processing video (extracting frames, transcribing, annotating)…"):
    process_video(video_path)
```

This gives the user feedback during the annotation step, which can take several minutes for longer videos.

- [ ] **Step 9: Final commit and push**

```bash
git add -A
git status   # confirm nothing unexpected
git push origin feature/specialized-signal-detection
```
