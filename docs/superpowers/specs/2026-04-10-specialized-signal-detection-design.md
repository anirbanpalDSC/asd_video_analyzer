# Design: Specialized Model Pre-Processing for ASD Signal Detection

**Date:** 2026-04-10
**Status:** Approved
**Branch:** feature/specialized-signal-detection

---

## Problem

The current pipeline sends raw JPEG frames to Gemma3 (a VLM) and relies entirely on its visual interpretation for all 10 signals. While Gemma3 can see and reason about images, it lacks precision for:

- **Signal 1 (gaze):** Estimating exact gaze angle or direction reliably across diverse camera angles
- **Signals 7/8/9 (motor):** Detecting specific posture geometry (wrist elevation, arm extension, rotational stance) quantitatively
- **Signal 6 (objects):** Detecting systematic object arrangements (linearity, symmetry) reliably
- **Signals 4/5 (language):** Grounding transcript evidence to specific frames rather than treating the full video as undifferentiated text

The result is inconsistent Yes/No/Unclear calls that are hard to validate or audit.

---

## Solution

Add a **pre-processing annotation layer** that runs specialized vision and language models on each frame at processing time, caches natural language annotations in `annotations.json`, and injects them into the VLM prompt at analysis time.

The VLM (Gemma3) remains the sole decision-maker — annotations provide precise measurements it uses as primary evidence. Signals 2 (Aggression) and 3 (Sensory Reactivity) have no reliable static-frame detector and remain VLM-only.

---

## Architecture

### New file — `src/annotator.py`

Owns all specialized model loading and inference. Public interface:

```python
def annotate_frames(
    thumb_paths: list[Path],
    transcript_json: Path | None,
    fps: float,
) -> dict[str, dict[str, str]]
```

Returns `{filename: {domain: natural_language_string}}`.

Models are loaded once into module-level globals (lazy, on first call). GPU is used automatically via PyTorch device detection (`torch.device("cuda" if torch.cuda.is_available() else "cpu")`).

### Modified — `src/processor.py`

After `generate_thumbnails()` completes, calls `annotate_frames()` on all extracted thumbnails and writes `processed/<video_stem>/thumbs/annotations.json`.

Idempotent: if `annotations.json` already exists, annotation is skipped (consistent with existing skip-if-processed pattern). Pass `force=True` to re-annotate.

### Modified — `src/analyzer.py`

When building the VLM message payload, loads `annotations.json` for the video and injects a `FRAME_ANNOTATIONS:` text block into the prompt immediately before the base64 images. Only the selected frames' annotations are included.

### Modified — `config/config.py`

- Adds `ANNOTATION_FPS` config constant (default: same as thumbnail extraction fps = 2.0; lower this for long videos to reduce annotation time)
- Updates `DEFAULT_ASD_PROMPT` to include `FRAME_ANNOTATIONS:` section with instructions

### Unchanged

`ui_utils.py`, `app.py`, all output parsing. The VLM still outputs `FRAME_DETECTIONS` + `SIGNALS` + `CLINICAL NARRATIVE` in the same format — annotations are input enrichment only.

---

## Models per Signal Domain

### Signal 1 — Gaze Direction (L2CS-Net)

**Model:** `l2cs_gaze360_resnet50` (pre-trained weights from HuggingFace, ~100 MB, downloaded once on first annotate run)

**Input:** Single JPEG frame
**Output:** Yaw and pitch gaze angles in degrees

**Natural language annotation examples:**
```
"Gaze directed 32° left of camera, 8° downward. No visible social target in frame."
"Gaze directed toward camera centre (yaw 3°, pitch -2°). Possible eye contact."
"Face not detected — gaze unassessable."
```

---

### Signals 7, 8, 9 — Body and Hand Pose (MediaPipe Pose + Hands)

**Models:** MediaPipe Pose (33 body landmarks) + MediaPipe Hands (21 landmarks per hand)

**Computed geometry from keypoints:**
- Wrist elevation relative to shoulder (signal 9 — flapping)
- Arm extension angle and bilateral symmetry (signal 9)
- Hand-to-body contact regions (signal 7)
- Rotational stance: feet planted, torso twist, arm spread (signal 8)

**Natural language annotation examples:**
```
"Both wrists elevated above shoulders, arms extended laterally without object contact. Consistent with mid-flap posture."
"Right hand in contact with left forearm region. No object detected in hand."
"Body rotational stance: torso twist with arms outstretched. Consistent with mid-spin posture."
"Pose not detected — body not visible in frame."
"Pose detected. No atypical posture patterns identified."
```

---

### Signal 6 — Object Arrangement (YOLOv8m)

**Model:** YOLOv8m (medium variant, ~50 MB). AGPL-3.0 license — suitable for research use.

**Detection logic:**
- Detect all objects in frame with bounding boxes
- Check for linear/symmetric arrangements of same-class objects (≥3 objects, collinearity threshold)
- Flag round/wheel-class objects that may indicate spinning objects

**Natural language annotation examples:**
```
"4 objects of class 'cup' detected in a linear arrangement along the lower frame edge."
"Spinning object detected: round object (class 'ball') with motion blur consistent with rotation."
"No linear or symmetric object arrangement detected."
"No objects detected in frame."
```

---

### Signals 4, 5 — Language (Whisper word timestamps + NLP)

**Approach:** Whisper is re-run with `word_timestamps=True`, saving a `.words.json` alongside the existing `.txt` transcript. Each thumbnail's timestamp is derived from its filename and extraction fps:

```
timestamp(thumb_N.jpg) = (N - 1) / fps
```

For each frame, extract transcript words within a ±3 second window around the frame timestamp. Run pattern matching on that window:

- **Signal 4 (Non-Responsiveness to Verbal Interaction):** Detect absence of speech response within window when prior context suggests a question or prompt
- **Signal 5 (Non-Typical Language):** Detect echolalia (repeated phrase sequences ≥ 2 repetitions), pronoun reversal ("you" used for self), scripted/delayed echolalia patterns

**Natural language annotation examples:**
```
"t=12s window: subject says 'go go go go' (4 repetitions of 'go'). Possible echolalia."
"t=12s window: no speech detected near this frame."
"t=12s window: speech present — 'I want the ball'. No atypical patterns detected."
"t=12s window: pronoun reversal candidate — subject says 'you want juice' in apparent self-reference context."
```

Language annotation is computed once per video and mapped to all frames by timestamp window. If Whisper was previously run without word timestamps, re-run is triggered automatically (`.words.json` absence detected).

---

## Prompt Injection

### New `FRAME_ANNOTATIONS:` section in `DEFAULT_ASD_PROMPT`

Inserted before the output format instructions. At analysis time, `analyzer.py` populates the template with actual annotation values:

```
FRAME_ANNOTATIONS:
(Pre-computed measurements from specialized vision and language models.
These complement your own visual analysis. For quantitative claims —
gaze angle, object count, transcript content, posture geometry — weight
these annotations more heavily than visual estimation alone.
If an annotation states a condition is unassessable, mark the signal Unclear.)

Frame_1:
  gaze: Gaze directed 32° left of camera, 8° downward. No visible social target.
  pose: Both wrists elevated above shoulders, arms extended laterally without object contact.
  objects: No linear object arrangement detected.
  language: t=4s window — subject says "go go go go" (4 repetitions). Possible echolalia.

Frame_2:
  gaze: Face not detected — gaze unassessable.
  pose: Pose not detected — body not visible.
  objects: 3 objects of class 'bottle' in linear arrangement along lower frame edge.
  language: t=8s window — no speech detected near this frame.
```

### Signals not covered by annotations

Signals 2 (Aggression) and 3 (Sensory Reactivity) have no annotation entry — the VLM assesses them from the image directly as before. The prompt makes this explicit so the VLM does not treat missing annotations as evidence of absence.

---

## Scaling

| Video length | Frames at 2 fps | Annotation time (GPU) |
|---|---|---|
| 2 min | 240 | ~30 sec |
| 10 min | 1,200 | ~2.5 min |
| 30 min | 3,600 | ~7 min |
| 60 min | 7,200 | ~14 min |

Annotation time is a one-time cost per video (cached). The VLM analysis call is always bounded by the user's frame selection (typically 5–15 frames) regardless of video length.

For long videos, `ANNOTATION_FPS` in `config/config.py` can be lowered (e.g., 1.0) to halve annotation time. When `ANNOTATION_FPS` is lower than the thumbnail extraction rate, `processor.py` annotates only every Nth thumbnail (stride = extraction_fps / annotation_fps). Non-annotated thumbnails are still displayed in the UI and selectable — they simply have no `FRAME_ANNOTATIONS` entry injected into the VLM prompt for that frame.

A progress indicator will be added to the Streamlit UI during the annotation step.

---

## New Dependencies

| Package | Purpose | License |
|---|---|---|
| `l2cs` | Gaze angle estimation | MIT |
| `mediapipe` | Pose + hand landmarks | Apache 2.0 |
| `ultralytics` | YOLOv8 object detection | AGPL-3.0 (research OK) |
| `torch` / `torchvision` | GPU inference backend (likely already installed) | BSD |

All weights are downloaded automatically on first run and cached locally.

---

## Scope

| File | Change |
|---|---|
| `src/annotator.py` | New — all model loading and annotation logic |
| `src/processor.py` | Call `annotate_frames()` after thumbnail extraction; save `annotations.json` |
| `src/analyzer.py` | Load `annotations.json`; inject `FRAME_ANNOTATIONS:` block into prompt |
| `config/config.py` | Add `ANNOTATION_FPS`; update `DEFAULT_ASD_PROMPT` with `FRAME_ANNOTATIONS:` section |
| All other files | No change |

---

## Trade-offs

| Option | Verdict |
|---|---|
| MediaPipe-only (all domains) | Not selected — MediaPipe Face Mesh is a gaze proxy, not a gaze estimator; L2CS-Net is more accurate for signal 1 |
| Best-in-class per domain (MediaPipe pose + L2CS-Net gaze + YOLOv8 + NLP) | **Selected** — accuracy vs. complexity balance |
| MMPose instead of MediaPipe Pose | Not selected — marginal accuracy gain over MediaPipe Pose for posture-based detection; heavier dependency tree |
| Replace VLM for annotated signals | Not selected — VLM holistic scene understanding (context, affect, interaction quality) complements rather than duplicates specialized models |

---

## Success Criteria

- Signal 1 annotations include quantitative gaze angles for frames where face is visible
- Signals 7/8/9 annotations describe specific posture geometry rather than generic "pose detected"
- Signal 6 annotations correctly identify linear object arrangements in test frames
- Signals 4/5 annotations align to the correct temporal window per frame
- VLM analysis incorporates annotation evidence in its signal assessments (verifiable in CLINICAL NARRATIVE)
- No change to output format — `ui_utils.py` parsing is unaffected
- Annotation step is idempotent — re-running `process_video()` does not re-annotate if `annotations.json` exists
