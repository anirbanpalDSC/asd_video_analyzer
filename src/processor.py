"""Video/audio processing utilities.

Functions mirror the behavior of the PHP scripts from the autismV project
(processVideo.php/processAudio.php) but are implemented in Python for use by
Streamlit.  External commands (ffmpeg, whisper) are discovered via
``u_utils`` so the paths are configurable.
"""

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
            
            # Generate unique filename
            unique_name = f"{video_title}_{uuid.uuid4().hex[:8]}.mp4"
            save_path = UPLOADS_DIR / unique_name
            
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
    """Run whisper CLI to transcribe the given mp3 into a .txt file next to it.

    Uses CUDA when available and compatible, otherwise falls back to CPU.
    Returns path to the transcript or None if the binary was missing / failed.
    """
    if dry_run:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)

    devices = ['cuda', 'cpu'] if _cuda_available() else ['cpu']
    for device in devices:
        cmd = [*u_utils.WHISPER_CMD,
               '--device', device,
               '--model', 'base',  # Use 'base' for faster processing; change to 'large' if needed
               '--task', 'transcribe',
               '--output_format', 'txt',
               '--output_dir', str(output_dir),
               str(mp3_path)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                # Success! locate and return text file
                text_path = output_dir / (mp3_path.stem + '.txt')
                if text_path.is_file():
                    return text_path
                else:
                    # Command succeeded but no output file created (rare edge case)
                    return None
            else:
                # Command failed; log error and try next device
                print(f"[whisper {device}] Failed with return code {result.returncode}")
                print(f"[whisper stderr] {result.stderr}")
                continue
        except FileNotFoundError:
            # Whisper binary not found at all
            return None
        except subprocess.TimeoutExpired:
            print(f"[whisper {device}] Timeout after 10 minutes")
            continue
        except Exception as e:
            print(f"[whisper {device}] Exception: {e}")
            continue
    
    # All attempts failed
    return None


def process_video(video_path: Path, force: bool = False) -> None:
    """Perform the full pipeline for a single upload.

    * create processed/<basename>/ and thumbs/ subdirectory
    * convert video -> mp3
    * extract thumbnails
    * run whisper to transcribe audio (if whisper is available)

    If ``force`` is False the directory is skipped when it already exists.
    """
    ensure_dirs()
    target = get_processed_folder(video_path.name)
    thumbs = target / 'thumbs'
    transcript_path = target / (video_path.stem + '.txt')
    if target.exists() and transcript_path.is_file() and not force:
        return
    target.mkdir(parents=True, exist_ok=True)
    thumbs.mkdir(parents=True, exist_ok=True)

    mp3_out = target / (video_path.stem + '.mp3')
    convert_to_mp3(video_path, mp3_out)
    generate_thumbnails(video_path, thumbs)
    # transcription is best‑effort
    transcribe_mp3(mp3_out, target)


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
        txt = proc / (Path(video_filename).stem + '.txt')
        if txt.is_file():
            try:
                info['transcript'] = txt.read_text(encoding='utf-8')
            except Exception:
                info['transcript'] = None
    return info
