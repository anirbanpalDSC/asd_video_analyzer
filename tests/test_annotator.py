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
        {"word": "hello", "start": 2.5, "end": 3.0},   # midpoint 2.75 — inside window
        {"word": "world", "start": 5.0, "end": 5.5},   # midpoint 5.25 — inside window
        {"word": "bye",   "start": 15.0, "end": 15.5}, # midpoint 15.25 — outside window
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


# ---------------------------------------------------------------------------
# _thumb_timestamp
# ---------------------------------------------------------------------------

def test_thumb_timestamp_first_frame():
    from src.annotator import _thumb_timestamp
    from pathlib import Path
    # thumb_00001.jpg at 2.0 fps → (1-1)/2.0 = 0.0s
    assert _thumb_timestamp(Path("thumb_00001.jpg"), fps=2.0) == 0.0


def test_thumb_timestamp_frame_12():
    from src.annotator import _thumb_timestamp
    from pathlib import Path
    # thumb_00012.jpg at 2.0 fps → (12-1)/2.0 = 5.5s
    assert _thumb_timestamp(Path("thumb_00012.jpg"), fps=2.0) == 5.5
