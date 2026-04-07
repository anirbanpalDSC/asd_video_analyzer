"""LLM interaction and prompt composition utilities.

This module constructs the same multi-message payload as the PHP code from
`autismV/index.php` and sends it to the remote API defined in
``config.API_URL``.  It supports adding a transcript and any number of base64
encoded thumbnails.
"""

import base64
import json
from pathlib import Path
from typing import List, Optional

import requests

from config.config import API_URL, DEFAULT_ASD_PROMPT


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

    payload = {"model": "gemma3:27b-it-fp16", "messages": messages, "stream": False, "options": {"temperature": 0, "top_k": 1, "seed": 42}}

    r = requests.post(API_URL, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    return data.get("message", {}).get("content", "").strip()
