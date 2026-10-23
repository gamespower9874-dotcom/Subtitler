# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local transcription using faster-whisper with VAD and JP-friendly defaults."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..base import Segment


@dataclass(frozen=True)
class _VADParams:
    """VAD filter settings keyed off the user-facing sensitivity knob."""

    min_silence_duration_ms: int
    speech_pad_ms: int
    threshold: float


_VAD_PRESETS: dict[str, _VADParams] = {
    # Aggressive: drop long silences, trim trailing/floating chunks.
    "aggressive": _VADParams(min_silence_duration_ms=300, speech_pad_ms=120, threshold=0.45),
    # Balanced default: standard Silero behaviour.
    "balanced": _VADParams(min_silence_duration_ms=500, speech_pad_ms=200, threshold=0.5),
    # Conservative: keep more speech, avoid cutting lines.
    "conservative": _VADParams(min_silence_duration_ms=700, speech_pad_ms=300, threshold=0.6),
}


@dataclass(frozen=True)
class _QualityThresholds:
    """Per-segment quality gates derived from Whisper confidence fields."""

    no_speech_prob: float
    avg_logprob: float
    compression_ratio: float


_QUALITY_PRESETS: dict[str, _QualityThresholds] = {
    "aggressive": _QualityThresholds(no_speech_prob=0.5, avg_logprob=-0.6, compression_ratio=1.6),
    "balanced": _QualityThresholds(no_speech_prob=0.6, avg_logprob=-0.8, compression_ratio=1.8),
    "conservative": _QualityThresholds(no_speech_prob=0.75, avg_logprob=-1.0, compression_ratio=2.2),
}


class FasterWhisperEngine:
    """Lazy wrapper around faster_whisper.WhisperModel.

    The model is imported on first use so that the rest of the application
    (tests, CLI help, packaging) does not require faster-whisper to be
    installed unless the local mode is actually exercised.
    """

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "auto",
        compute_type: str = "auto",
        sensitivity: str = "balanced",
    ) -> None:
        if sensitivity not in _VAD_PRESETS:
            raise ValueError(f"Unknown sensitivity: {sensitivity!r}")
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.sensitivity = sensitivity
        self._model: Any | None = None

    def _ensure_model(self) -> Any:
        if self._model is not None:
            return self._model
        from faster_whisper import WhisperModel  # type: ignore[import-not-found]

        kwargs: dict[str, Any] = {}
        if self.device != "auto":
            kwargs["device"] = self.device
        if self.compute_type != "auto":
            kwargs["compute_type"] = self.compute_type
        self._model = WhisperModel(self.model_size, **kwargs)
        return self._model

    def transcribe(
        self,
        audio_path: str,
        source_language: str | None = "ja",
        glossary: str = "",
    ) -> list[Segment]:
        model = self._ensure_model()
        vad = _VAD_PRESETS[self.sensitivity]
        quality = _QUALITY_PRESETS[self.sensitivity]

        segments_iter, _info = model.transcribe(
            str(Path(audio_path)),
            language=source_language,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": vad.min_silence_duration_ms,
                "speech_pad_ms": vad.speech_pad_ms,
                "threshold": vad.threshold,
            },
            condition_on_previous_text=False,
            word_timestamps=False,
            initial_prompt=glossary or None,
        )

        output: list[Segment] = []
        for seg in segments_iter:
            no_speech = float(getattr(seg, "no_speech_prob", 0.0))
            avg_logprob = float(getattr(seg, "avg_logprob", 0.0))
            compression = float(getattr(seg, "compression_ratio", 1.0))
            if no_speech > quality.no_speech_prob:
                continue
            if avg_logprob < quality.avg_logprob:
                continue
            if compression > quality.compression_ratio:
                continue
            output.append(
                {
                    "start": float(seg.start),
                    "end": float(seg.end),
                    "text": (seg.text or "").strip(),
                    "speaker": None,
                    "no_speech_prob": no_speech,
                    "avg_logprob": avg_logprob,
                    "compression_ratio": compression,
                }
            )
        return output
