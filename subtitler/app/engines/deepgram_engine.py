# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deepgram Nova-2 transcription with utterances and diarization."""
import os
from deepgram import DeepgramClient, PrerecordedOptions
from .base import Segment

class DeepgramEngine:
    def __init__(self, api_key: str | None = None):
        self.client = DeepgramClient(api_key or os.getenv("DEEPGRAM_API_KEY"))

    def transcribe(self, audio_path: str, source_language: str | None = None, glossary: str = "") -> list[Segment]:
        with open(audio_path, "rb") as handle:
            result = self.client.listen.rest.v("1").transcribe_file({"buffer": handle.read()}, PrerecordedOptions(model="nova-2", language=source_language or "multi", diarize=True, utterances=True, smart_format=True))
        utterances = getattr(getattr(getattr(result, "results", None), "utterances", None), "items", []) or []
        return [{"start": float(u.start), "end": float(u.end), "text": u.transcript.strip(), "speaker": str(u.speaker) if getattr(u, "speaker", None) is not None else None} for u in utterances]
