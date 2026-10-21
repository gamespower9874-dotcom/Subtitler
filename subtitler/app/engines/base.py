# SPDX-License-Identifier: AGPL-3.0-or-later
"""Common transcription types."""
from typing import Protocol, TypedDict

class Segment(TypedDict, total=False):
    start: float
    end: float
    text: str
    speaker: str | None

class TranscriptionEngine(Protocol):
    def transcribe(self, audio_path: str, source_language: str | None = None, glossary: str = "") -> list[Segment]: ...
