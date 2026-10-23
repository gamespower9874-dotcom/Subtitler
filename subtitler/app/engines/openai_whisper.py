# SPDX-License-Identifier: AGPL-3.0-or-later
"""OpenAI Whisper transcription with large-file chunking."""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from openai import OpenAI

from ..base import Segment
from ..secrets import Secrets


class OpenAIWhisperEngine:
    def __init__(self, api_key: str | None = None, secrets: Secrets | None = None):
        secrets = secrets or Secrets()
        key = api_key or secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        # ``OpenAI`` does not expose the key in its ``__repr__`` but we
        # still keep the client local to this request so it cannot leak
        # into another engine or run.
        self._secrets = secrets
        self.client = OpenAI(api_key=key)

    def transcribe(
        self,
        audio_path: str,
        source_language: str | None = None,
        glossary: str = "",
    ) -> list[Segment]:
        path = Path(audio_path)
        if path.stat().st_size <= 25 * 1024 * 1024:
            return self._one(path, 0, source_language, glossary)
        segments: list[Segment] = []
        with tempfile.TemporaryDirectory() as temp:
            pattern = str(Path(temp) / "part_%03d.wav")
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(path), "-f", "segment", "-segment_time", "600", pattern],
                check=True,
                capture_output=True,
            )
            for part in sorted(Path(temp).glob("part_*.wav")):
                offset = len(segments) and segments[-1]["end"] or 0
                segments.extend(self._one(part, float(offset), source_language, glossary))
        return segments

    def _one(self, path: Path, offset: float, language: str | None, glossary: str) -> list[Segment]:
        with path.open("rb") as handle:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=handle,
                response_format="verbose_json",
                language=language,
                prompt=glossary or None,
            )
        return [
            {
                "start": float(item.start) + offset,
                "end": float(item.end) + offset,
                "text": item.text.strip(),
                "speaker": None,
            }
            for item in response.segments
        ]
