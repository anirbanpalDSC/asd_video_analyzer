"""LLM interaction and prompt composition utilities.

This module constructs the same multi-message payload as the PHP code from
`autismV/index.php` and sends it to the remote API defined in
``config.API_URL``.  It supports adding a transcript and any number of base64
encoded thumbnails.
"""

import base64
import json
import time
from pathlib import Path
from typing import Generator, List, Optional

import requests

from config.config import API_URL, DEFAULT_ASD_PROMPT

# Hard ceiling on total generation time (seconds)
_MAX_GENERATION_SECS = 300


def _encode_images(paths: List[Path]) -> List[str]:
    b64_list = []
    for p in paths:
        try:
            data = p.read_bytes()
            b64_list.append(base64.b64encode(data).decode('ascii'))
        except Exception:
            # skip files we cannot read
            continue
    return b64_list


def _build_frame_annotations_block(
    selected_thumb_paths: list,
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


def _load_annotations(selected_thumb_paths: list) -> dict:
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



def analyze(
    video: str,
    user_prompt: Optional[str] = None,
    selected_thumb_paths: Optional[List[Path]] = None,
    transcript: Optional[str] = None,
) -> str:
    """Send data to the LLM API and return the model's response text.

    Parameters
    ----------
    video
        The base filename of the video (used for context only).
    user_prompt
        Custom prompt entered by the user; if None the ASD default is used.
    selected_thumb_paths
        Paths to the thumbnail files that should be attached.
    transcript
        Pre‑loaded transcript text (may be truncated already).
    """
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

    # Build image list
    img_b64_list = _encode_images(selected_thumb_paths or [])
    
    # For vision models, embed images in the user content message
    # using the standard format with image tokens
    if img_b64_list:
        # Insert image tokens in the prompt so the model processes them
        content = prompt + f"\n\n[Processing {len(img_b64_list)} video frames for behavioral analysis]\n"
        for _ in img_b64_list:
            content += "[image]\n"
        
        messages = [{"role": "user", "content": content, "images": img_b64_list}]
    else:
        messages = [{"role": "user", "content": prompt}]

    payload = {
        "model": "gemma3:27b-it-fp16",
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0, "seed": 42},
    }

    r = requests.post(API_URL, json=payload, timeout=(30, 120), stream=True)
    r.raise_for_status()

    deadline = time.time() + _MAX_GENERATION_SECS
    chunks: List[str] = []
    for line in r.iter_lines():
        if time.time() > deadline:
            raise TimeoutError(
                f"Analysis exceeded {_MAX_GENERATION_SECS}s limit — "
                "try selecting fewer frames."
            )
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        token = obj.get("message", {}).get("content", "")
        chunks.append(token)
        if obj.get("done") or obj.get("done_reason") == "stop":
            break

    return "".join(chunks).strip()


def analyze_stream(
    video: str,
    user_prompt: Optional[str] = None,
    selected_thumb_paths: Optional[List[Path]] = None,
    transcript: Optional[str] = None,
) -> Generator[str, None, None]:
    """Same as analyze() but yields text tokens as they arrive.

    Callers should collect the yielded chunks to obtain the full response.
    Raises on HTTP errors or timeout.
    """
    prompt = user_prompt or DEFAULT_ASD_PROMPT
    if transcript:
        prompt = f"{prompt}\n\nTranscript context:\n{transcript}"

    # Inject FRAME_ANNOTATIONS from cached specialized model output
    annotations = _load_annotations(selected_thumb_paths or [])
    fa_block = _build_frame_annotations_block(selected_thumb_paths or [], annotations)
    if fa_block:
        prompt = prompt + fa_block

    img_b64_list = _encode_images(selected_thumb_paths or [])

    if img_b64_list:
        content = prompt + f"\n\n[Processing {len(img_b64_list)} video frames for behavioral analysis]\n"
        for _ in img_b64_list:
            content += "[image]\n"
        messages = [{"role": "user", "content": content, "images": img_b64_list}]
    else:
        messages = [{"role": "user", "content": prompt}]

    payload = {
        "model": "gemma3:27b-it-fp16",
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0, "seed": 42},
    }

    r = requests.post(API_URL, json=payload, timeout=(30, 120), stream=True)
    r.raise_for_status()

    deadline = time.time() + _MAX_GENERATION_SECS
    for line in r.iter_lines():
        if time.time() > deadline:
            raise TimeoutError(
                f"Analysis exceeded {_MAX_GENERATION_SECS}s limit — "
                "try selecting fewer frames."
            )
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        token = obj.get("message", {}).get("content", "")
        if token:
            yield token
        if obj.get("done") or obj.get("done_reason") == "stop":
            return
