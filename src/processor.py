"""Video/audio processing utilities.

Functions mirror the behavior of the PHP scripts from the autismV project
(processVideo.php/processAudio.php) but are implemented in Python for use by
Streamlit.  External commands (ffmpeg, whisper) are discovered via
``u_utils`` so the paths are configurable.
"""

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional
import uuid

from config.config import UPLOADS_DIR, PROCESSED_DIR, ALLOWED_EXTENSIONS
from src import u_utils


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def download_video_from_url(url: str) -> Optional[str]:
    """Download a video from YouTube or Facebook and save it to uploads folder.
    
    Args:
        url: YouTube or Facebook video URL
        
    Returns:
        The saved filename if successful, None if download fails.
    """
    try:
        import yt_dlp
    except ImportError:
        return None
    
    ensure_dirs()
    
    try:
        # Configure yt-dlp to download best available format
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Prefer mp4
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info to determine extension
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'video').replace(' ', '_')[:50]

            # Deterministic filename based on URL — same URL never downloads twice
            url_hash = hashlib.md5(url.strip().encode()).hexdigest()[:8]
            unique_name = f"{video_title}_{url_hash}.mp4"
            save_path = UPLOADS_DIR / unique_name

            if save_path.exists():
                return unique_name

            # Download to temp location first
            ydl_opts['outtmpl'] = str(UPLOADS_DIR / 'temp_download')
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find downloaded file and rename
            temp_files = list(UPLOADS_DIR.glob('temp_download*'))
            if temp_files:
                temp_file = temp_files[0]
                temp_file.rename(save_path)
                return unique_name
            
        return None
        
    except Exception as e:
        print(f"[yt-dlp error] {e}")
        return None


def ensure_dirs() -> None:
    """Create upload/processed roots if they don't already exist."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def list_uploads() -> List[str]:
    """Return the base names of all videos in the uploads directory."""
    ensure_dirs()
    names = []
    for p in UPLOADS_DIR.iterdir():
        if p.is_file() and p.suffix.lower().lstrip('.') in ALLOWED_EXTENSIONS:
            names.append(p.name)
    return sorted(names, key=lambda s: s.lower())


def get_processed_folder(video_filename: str) -> Path:
    """Return the folder under processed/ corresponding to the given upload.

    The PHP version created a directory named after the original file's
    basename (without extension).
    """
    base = Path(video_filename).stem
    return PROCESSED_DIR / base


def convert_to_mp3(video_path: Path, mp3_path: Path) -> bool:
    """Run ffmpeg to convert the video file to mp3 audio.

    Returns True on success (file exists afterward).
    """
    cmd = [u_utils.FFMPEG_CMD, '-y', '-i', str(video_path), '-vn',
           '-acodec', 'libmp3lame', '-q:a', '2', str(mp3_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and mp3_path.is_file()


def generate_thumbnails(video_path: Path, thumbs_dir: Path, fps: float = 2.0) -> bool:
    """Extract frames from the video at a given frames‑per‑second rate.

    Output files are named thumb_00001.jpg etc.
    Returns True if at least one thumbnail was produced.
    """
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(thumbs_dir / 'thumb_%05d.jpg')
    cmd = [u_utils.FFMPEG_CMD, '-y', '-i', str(video_path),
           '-vf', f'fps={fps}', '-q:v', '2', pattern]
    result = subprocess.run(cmd, capture_output=True, text=True)
    matches = list(thumbs_dir.glob('thumb_*.jpg'))
    return result.returncode == 0 and bool(matches)


def _cuda_available() -> bool:
    """Return True only if torch reports CUDA is available AND a kernel smoke-test passes."""
    try:
        import torch
        if not torch.cuda.is_available():
            return False
        # A minimal tensor op catches compute-capability mismatches before whisper tries to load
        torch.zeros(1, device='cuda')
        return True
    except Exception:
        return False


def transcribe_mp3(mp3_path: Path, output_dir: Path, dry_run: bool = False) -> Optional[Path]:
    """Transcribe the given mp3 using the whisper Python API.

    Uses CUDA when available, otherwise CPU.
    Returns path to the transcript .txt or None on failure.
    """
    if dry_run:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    text_path = output_dir / (mp3_path.stem + '.txt')

    try:
        import whisper as _whisper
        device = 'cuda' if _cuda_available() else 'cpu'
        model = _whisper.load_model('base', device=device,
                                    download_root=u_utils.WHISPER_CACHE_DIR)
        result = model.transcribe(str(mp3_path))
        text_path.write_text(result['text'].strip(), encoding='utf-8')
        return text_path
    except ImportError:
        print("[whisper] Python module not available, falling back to CLI")
    except Exception as e:
        print(f"[whisper python api] {e}")
        return None

    # CLI fallback (e.g. conda env where module isn't importable directly)
    devices = ['cuda', 'cpu'] if _cuda_available() else ['cpu']
    for device in devices:
        cmd = [*u_utils.WHISPER_CMD,
               '--device', device,
               '--model', 'base',
               '--task', 'transcribe',
               '--output_format', 'txt',
               '--output_dir', str(output_dir),
               str(mp3_path)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0 and text_path.is_file():
                return text_path
            print(f"[whisper cli {device}] rc={result.returncode} {result.stderr[:200]}")
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            print(f"[whisper cli {device}] timeout")
        except Exception as e:
            print(f"[whisper cli {device}] {e}")

    return None


def _extract_youtube_id(url: str) -> Optional[str]:
    """Return the YouTube video ID from any common YouTube URL format, or None."""
    import re
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def transcribe_from_youtube(url: str, output_dir: Path, stem: str) -> Optional[Path]:
    """Fetch the transcript for a YouTube video using the YouTube Transcript API.

    Writes both a plain .txt and a .words.json (in the same schema as Whisper's
    word-timestamp output) so the rest of the pipeline treats it identically.

    Returns the path to the .words.json on success, or None on any failure.
    """
    import json as _json

    video_id = _extract_youtube_id(url)
    if not video_id:
        print(f"[youtube-transcript] Could not extract video ID from {url!r}")
        return None

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("[youtube-transcript] youtube-transcript-api not installed")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    txt_path  = output_dir / (stem + ".txt")
    json_path = output_dir / (stem + ".words.json")

    try:
        api = YouTubeTranscriptApi()

        # Prefer manually-created captions; fall back to auto-generated
        transcript_list = api.list(video_id)
        try:
            transcript = transcript_list.find_manually_created_transcript(
                ["en", "en-US", "en-GB"]
            )
            source = "manual"
        except Exception:
            transcript = transcript_list.find_generated_transcript(
                ["en", "en-US", "en-GB"]
            )
            source = "auto-generated"

        entries = transcript.fetch()

        # Build words.json in Whisper-compatible schema
        segments_out = []
        plain_parts  = []
        for entry in entries:
            text  = getattr(entry, "text", "").strip()
            start = float(getattr(entry, "start", 0.0))
            dur   = float(getattr(entry, "duration", 0.0))
            end   = start + dur
            plain_parts.append(text)
            # YouTube captions don't have per-word timestamps; emit each
            # caption chunk as a single-word entry so downstream code works.
            segments_out.append({
                "start": start,
                "end":   end,
                "text":  text,
                "words": [{"word": text, "start": start, "end": end}],
            })

        plain_text = " ".join(plain_parts)
        txt_path.write_text(plain_text, encoding="utf-8")
        json_path.write_text(
            _json.dumps({"segments": segments_out, "_source": f"youtube-{source}"},
                        ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[youtube-transcript] fetched {source} captions for {video_id}")
        return json_path

    except Exception as e:
        print(f"[youtube-transcript] {type(e).__name__}: {e}")
        return None


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
        # Also write the plain .txt so get_video_info() can find the transcript
        plain_text = result.get("text", "").strip()
        txt_path = output_dir / (mp3_path.stem + ".txt")
        txt_path.write_text(plain_text, encoding="utf-8")
        return json_path
    except Exception as e:
        print(f"[whisper word timestamps] {e}")
        return None


def process_video(video_path: Path, force: bool = False,
                  source_url: Optional[str] = None) -> None:
    """Perform the full pipeline for a single upload.

    * create processed/<basename>/ and thumbs/ subdirectory
    * convert video -> mp3
    * extract thumbnails at 2 fps
    * transcribe audio:
        - URL inputs: YouTube Transcript API first (instant, higher quality),
          fall back to Whisper if unavailable or failed
        - File uploads: Whisper only
    * run specialized model annotation on thumbnails

    If ``force`` is False the full pipeline is skipped when already processed,
    but annotation is still run if annotations.json is missing.
    ``source_url`` is the original URL the video was downloaded from (YouTube /
    Facebook). When provided, the YouTube Transcript API is tried first.
    """
    import json as _json
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
                _json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return

    target.mkdir(parents=True, exist_ok=True)
    thumbs.mkdir(parents=True, exist_ok=True)

    mp3_out = target / (video_path.stem + ".mp3")
    convert_to_mp3(video_path, mp3_out)
    generate_thumbnails(video_path, thumbs)

    # Transcription — priority order depends on source
    # YouTube URL → try YouTube Transcript API first (no audio processing needed,
    # higher quality captions), fall back to Whisper on failure.
    # File upload → Whisper only.
    transcript_done = False
    if source_url and _extract_youtube_id(source_url):
        transcript_done = bool(
            transcribe_from_youtube(source_url, target, video_path.stem)
        )
        if not transcript_done:
            print("[process_video] YouTube transcript unavailable, falling back to Whisper")

    if not transcript_done:
        # Whisper with word timestamps; plain .txt fallback if that also fails
        if not transcribe_mp3_with_timestamps(mp3_out, target):
            transcribe_mp3(mp3_out, target)

    # Annotation — run after thumbnails and transcript are ready
    thumb_list = sorted(thumbs.glob("thumb_*.jpg"))
    result = annotate_frames(
        thumb_list,
        words_json_path if words_json_path.exists() else None,
        fps=2.0,
    )
    annotations_path.write_text(
        _json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def delete_video(video_filename: str) -> bool:
    """Delete a video and all its processed artifacts.

    Removes the upload file and the entire processed/<stem>/ directory.
    Returns True if both were removed (or were already absent).
    """
    upload_path = UPLOADS_DIR / video_filename
    processed_path = get_processed_folder(video_filename)

    ok = True
    try:
        if upload_path.is_file():
            upload_path.unlink()
    except Exception as e:
        print(f"[delete_video] Could not remove upload: {e}")
        ok = False
    try:
        if processed_path.is_dir():
            shutil.rmtree(processed_path)
    except Exception as e:
        print(f"[delete_video] Could not remove processed folder: {e}")
        ok = False
    return ok


def get_video_info(video_filename: str) -> dict:
    """Return metadata about a processed video suitable for display.

    The dictionary contains keys: ``mp3``, ``thumbs`` (list of Path),
    ``transcript`` (str or None).
    """
    info = {'mp3': None, 'thumbs': [], 'transcript': None}
    proc = get_processed_folder(video_filename)
    if proc.is_dir():
        mp3 = proc / (Path(video_filename).stem + '.mp3')
        if mp3.is_file():
            info['mp3'] = mp3
        info['thumbs'] = sorted(proc.glob('thumbs/thumb_*.jpg'))
        stem = Path(video_filename).stem
        txt = proc / (stem + '.txt')
        if txt.is_file():
            try:
                info['transcript'] = txt.read_text(encoding='utf-8')
            except Exception:
                info['transcript'] = None
        else:
            # Fall back to words.json if plain .txt was never written
            words_json = proc / (stem + '.words.json')
            if words_json.is_file():
                try:
                    import json as _json
                    data = _json.loads(words_json.read_text(encoding='utf-8'))
                    info['transcript'] = " ".join(
                        seg.get("text", "") for seg in data.get("segments", [])
                    ).strip()
                except Exception:
                    info['transcript'] = None
    return info
