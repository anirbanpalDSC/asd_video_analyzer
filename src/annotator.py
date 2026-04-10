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


def _download_model_if_needed(model_path, model_url) -> None:
    """Download a MediaPipe Tasks model bundle if not already present."""
    if model_path.exists():
        return
    import urllib.request
    model_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(model_url, model_path)


def _load_pose_model():
    global _pose_model
    if _pose_model is not None:
        return _pose_model
    import mediapipe as mp
    from config.config import POSE_MODEL_PATH, POSE_MODEL_URL
    _download_model_if_needed(POSE_MODEL_PATH, POSE_MODEL_URL)
    options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(POSE_MODEL_PATH)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
    )
    _pose_model = mp.tasks.vision.PoseLandmarker.create_from_options(options)
    return _pose_model


def _load_hands_model():
    global _hands_model
    if _hands_model is not None:
        return _hands_model
    import mediapipe as mp
    from config.config import HANDS_MODEL_PATH, HANDS_MODEL_URL
    _download_model_if_needed(HANDS_MODEL_PATH, HANDS_MODEL_URL)
    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(HANDS_MODEL_PATH)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.5,
    )
    _hands_model = mp.tasks.vision.HandLandmarker.create_from_options(options)
    return _hands_model


def _annotate_pose(frame_bgr: np.ndarray) -> str:
    """Return a natural language posture description from MediaPipe landmarks."""
    try:
        import mediapipe as mp
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        pose = _load_pose_model()
        pose_results = pose.detect(mp_image)

        hands = _load_hands_model()
        hands_results = hands.detect(mp_image)

        if not pose_results.pose_landmarks:
            return "Pose not detected — body not visible in frame."

        lm = pose_results.pose_landmarks[0]

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
        l_arm_extended = abs(l_wrist.x - l_shoulder.x) > shoulder_width * 0.8
        r_arm_extended = abs(r_wrist.x - r_shoulder.x) > shoulder_width * 0.8
        hip_width      = abs(l_hip.x - r_hip.x)
        if l_arm_extended and r_arm_extended and shoulder_width > hip_width * 1.2:
            observations.append(
                "Body rotational stance: arms outstretched, shoulder span exceeds hip width — "
                "consistent with mid-spin posture (signal 8)."
            )

        # --- Signal 7: hand-to-body contact ---
        if hands_results.hand_landmarks:
            for hand_lm in hands_results.hand_landmarks:
                hw = hand_lm[0]
                torso_x_lo = min(l_shoulder.x, r_shoulder.x)
                torso_x_hi = max(l_shoulder.x, r_shoulder.x)
                torso_y_lo = min(l_shoulder.y, r_shoulder.y)
                torso_y_hi = max(l_hip.y, r_hip.y)
                in_torso_x = torso_x_lo - 0.1 <= hw.x <= torso_x_hi + 0.1
                in_torso_y = torso_y_lo - 0.1 <= hw.y <= torso_y_hi + 0.1
                if in_torso_x and in_torso_y:
                    observations.append(
                        "Hand in contact with torso region — "
                        "possible self-hitting evidence (signal 7)."
                    )
                if hw.y < min(l_shoulder.y, r_shoulder.y) - 0.05:
                    observations.append(
                        "Hand elevated near head region — "
                        "possible self-hitting evidence (signal 7)."
                    )

        if not observations:
            return "Pose detected. No atypical posture patterns identified."
        return " ".join(observations)

    except Exception as e:
        return f"Pose unassessable (error: {type(e).__name__})."


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

        # Flag round/spinning objects
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

    snippet = " ".join(w["word"] for w in window_words).strip()
    observations = [f"t={t_center:.0f}s window: speech — \"{snippet[:80]}\""]

    echolalia = _detect_echolalia(window_words)
    if echolalia:
        observations.append(echolalia)

    if _detect_pronoun_reversal(window_words):
        observations.append("pronoun reversal candidate ('you' used in first-person context).")

    return " ".join(observations)


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
