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
