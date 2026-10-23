# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deepgram Nova-2 transcription with utterances and diarization."""
from __future__ import annotations

import os

from ..base import Segment
from ..secrets import Secrets


class DeepgramEngine:
    def __init__(self, api_key: str | None = None, secrets: Secrets | None = None):
        # Lazy import: deepgram-sdk v4+ has a different API, but the package
        # only needs to be present when this engine is actually used.
        from deepgram import DeepgramClient

        secrets = secrets or Secrets()
        key = api_key or secrets.get("DEEPGRAM_API_KEY") or os.getenv("DEEPGRAM_API_KEY")
        self._secrets = secrets
        self.client = DeepgramClient(key)

    def transcribe(
        self,
        audio_path: str,
        source_language: str | None = None,
        glossary: str = "",
    ) -> list[Segment]:
        try:
            from deepgram import PrerecordedOptions
        except ImportError:  # pragma: no cover - newer SDK variant
            PrerecordedOptions = None
        options = (
            {
                "model": "nova-2",
                "language": source_language or "multi",
                "diarize": True,
                "utterances": True,
                "smart_format": True,
            }
            if PrerecordedOptions is None
            else PrerecordedOptions(
                model="nova-2",
                language=source_language or "multi",
                diarize=True,
                utterances=True,
                smart_format=True,
            )
        )
        with open(audio_path, "rb") as handle:
            result = self.client.listen.rest.v("1").transcribe_file({"buffer": handle.read()}, options)
        utterances = (
            getattr(getattr(getattr(result, "results", None), "utterances", None), "items", []) or []
        )
        return [
            {
                "start": float(u.start),
                "end": float(u.end),
                "text": u.transcript.strip(),
                "speaker": str(u.speaker) if getattr(u, "speaker", None) is not None else None,
            }
            for u in utterances
        ]
