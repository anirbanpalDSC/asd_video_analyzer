"""Central configuration for the ASD Video Analyzer app. All tunable parameters should be defined here."""

import glob
import os
import shutil
import sys
from pathlib import Path

#----------------------------------------------------------
# Ollama/LLM
#----------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-vl:7b" # Override in sidebar, but must be a vision compatible model. See https://ollama.com/models for a list of available models.

#----------------------------------------------------------
# CLI tools
#----------------------------------------------------------
# Path to ffmpeg binary. If not found, the app will attempt to use the system-installed ffmpeg. If you want to use a specific version of ffmpeg, set the path here
FFMPEG_CMD = shutil.which("ffmpeg") or "ffmpeg"  # Use system-installed ffmpeg if not found in PATH

# Whisper: auto-detect from PATH, then conda/venv environments, then Python module.
# If none found, transcription will gracefully fail.
_whisper_cli = shutil.which("whisper")
if not _whisper_cli:
    # Search conda environments and common virtualenv locations
    _search_patterns = [
        os.path.expanduser("~/miniconda3/envs/*/bin/whisper"),
        os.path.expanduser("~/anaconda3/envs/*/bin/whisper"),
        os.path.expanduser("~/miniforge3/envs/*/bin/whisper"),
        os.path.expanduser("~/miniconda3/bin/whisper"),
        os.path.expanduser("~/anaconda3/bin/whisper"),
    ]
    for _pattern in _search_patterns:
        _candidates = sorted(glob.glob(_pattern))
        if _candidates:
            _whisper_cli = _candidates[0]
            break

if _whisper_cli:
    WHISPER_CMD = [_whisper_cli]
else:
    # Try to use whisper Python module as fallback
    try:
        import whisper as _whisper_module
        # Use the module's CLI entry point via python -m
        WHISPER_CMD = [sys.executable, '-m', 'whisper']
    except ImportError:
        # Whisper not installed at all; set a default that will fail gracefully
        WHISPER_CMD = ['whisper']