# SPDX-License-Identifier: AGPL-3.0-or-later
"""OpenAI Whisper transcription with large-file chunking."""
from pathlib import Path
import os
import subprocess
import tempfile
from openai import OpenAI
from .base import Segment

class OpenAIWhisperEngine:
    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def transcribe(self, audio_path: str, source_language: str | None = None, glossary: str = "") -> list[Segment]:
        path = Path(audio_path)
        if path.stat().st_size <= 25 * 1024 * 1024:
            return self._one(path, 0, source_language, glossary)
        segments: list[Segment] = []
        with tempfile.TemporaryDirectory() as temp:
            pattern = str(Path(temp) / "part_%03d.wav")
            subprocess.run(["ffmpeg", "-y", "-i", str(path), "-f", "segment", "-segment_time", "600", pattern], check=True, capture_output=True)
            for part in sorted(Path(temp).glob("part_*.wav")):
                offset = len(segments) and segments[-1]["end"] or 0
                segments.extend(self._one(part, float(offset), source_language, glossary))
        return segments

    def _one(self, path: Path, offset: float, language: str | None, glossary: str) -> list[Segment]:
        with path.open("rb") as handle:
            response = self.client.audio.transcriptions.create(model="whisper-1", file=handle, response_format="verbose_json", language=language, prompt=glossary or None)
        return [{"start": float(item.start) + offset, "end": float(item.end) + offset, "text": item.text.strip(), "speaker": None} for item in response.segments]
