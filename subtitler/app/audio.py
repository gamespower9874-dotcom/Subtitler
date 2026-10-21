# SPDX-License-Identifier: AGPL-3.0-or-later
"""FFmpeg and FFprobe helpers for audio preparation."""
from pathlib import Path
import json
import subprocess


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, capture_output=True, text=True)


def list_tracks(video: str | Path) -> list[dict]:
    """Return audio/video stream metadata from FFprobe."""
    result = _run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(video)])
    return json.loads(result.stdout).get("streams", [])


def extract_master(video: str | Path, output: str | Path) -> Path:
    """Extract a 48 kHz, 24-bit PCM WAV master."""
    output = Path(output)
    _run(["ffmpeg", "-y", "-i", str(video), "-vn", "-ar", "48000", "-acodec", "pcm_s24le", str(output)])
    return output


def make_asr_audio(master: str | Path, output: str | Path) -> Path:
    """Make mono 16 kHz speech audio with a high-pass filter and loudness normalization."""
    output = Path(output)
    _run(["ffmpeg", "-y", "-i", str(master), "-af", "highpass=f=80,loudnorm", "-ar", "16000", "-ac", "1", str(output)])
    return output
