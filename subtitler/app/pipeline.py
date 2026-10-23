# SPDX-License-Identifier: AGPL-3.0-or-later
"""High-level subtitle pipeline (API + local, with post-processing)."""
from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .audio import extract_master, make_asr_audio
from .engines.deepgram_engine import DeepgramEngine
from .engines.faster_whisper_engine import FasterWhisperEngine
from .engines.openai_whisper import OpenAIWhisperEngine
from .ensemble import merge_passes
from .jp_postprocess import postprocess_jp
from .qc import check
from .run_report import FileReport, STATUS_DONE, STATUS_EMPTY, STATUS_FAILED
from .secrets import Secrets
from .subtitles import FORMAT_SRT, FORMAT_VTT, to_srt, to_vtt
from .translate import translate_segments


@dataclass
class PipelineResult:
    srt_path: Path
    master_wav_path: Path
    qc_report: list[tuple[int, str]]
    segments: list[dict]
    report: FileReport


def _resolve_engine(mode: str, sensitivity: str, model_size: str, secrets: Secrets):
    mode = (mode or "api").lower()
    if mode == "local":
        return FasterWhisperEngine(model_size=model_size, sensitivity=sensitivity)
    return OpenAIWhisperEngine(secrets=secrets)


def run_pipeline(
    video: str | Path,
    engine_name: str = "openai",
    source_language: str | None = None,
    target_language: str = "French",
    glossary: str = "",
    output_dir: str | Path | None = None,
    *,
    mode: str = "api",
    sensitivity: str = "balanced",
    model_size: str = "large-v3",
    output_format: str = "srt",
    provider: str | None = None,
    ensemble: bool = False,
    secrets: Secrets | None = None,
) -> PipelineResult:
    """Run the full pipeline.

    ``secrets`` carries API keys for **this run only**. The pipeline never
    persists them, logs them, or includes them in ``run.json``. Any
    exception message that bubbles up is scrubbed via
    :func:`Secrets.redact_string` before it lands in the report.
    """
    secrets = secrets or Secrets()
    out = Path(output_dir or tempfile.mkdtemp(prefix="subtitler-"))
    out.mkdir(parents=True, exist_ok=True)
    report = FileReport(input_path=str(video))

    try:
        master = extract_master(video, out / "master.wav")
        asr = make_asr_audio(master, out / "asr.wav")

        primary = _resolve_engine(mode, sensitivity, model_size, secrets)
        segments = primary.transcribe(str(asr), source_language, glossary)

        if ensemble and mode != "local":
            try:
                if engine_name.lower() != "deepgram":
                    secondary_engine = DeepgramEngine(secrets=secrets)
                else:
                    secondary_engine = OpenAIWhisperEngine(secrets=secrets)
                secondary = secondary_engine.transcribe(str(asr), source_language, glossary)
                segments = merge_passes(segments, secondary)
            except Exception:
                pass

        if source_language and source_language.lower().startswith("ja"):
            segments = postprocess_jp(segments)

        translated = translate_segments(
            segments,
            target_language,
            glossary,
            provider=provider,
            secrets=secrets,
        )

        qc_report = check(translated)
        (out / "qc_report.json").write_text(json.dumps(qc_report, indent=2), encoding="utf-8")

        fmt = (output_format or FORMAT_SRT).lower()
        if fmt == "both":
            srt_path = to_srt(translated, out / "subtitles.srt")
            to_vtt(translated, out / "subtitles.vtt")
        elif fmt == FORMAT_VTT:
            srt_path = to_vtt(translated, out / "subtitles.vtt")
        else:
            srt_path = to_srt(translated, out / "subtitles.srt")

        status = STATUS_EMPTY if not translated else STATUS_DONE
        duration = sum(float(seg.get("end", 0)) - float(seg.get("start", 0)) for seg in translated)
        report.finish(
            status=status,
            output_path=str(srt_path),
            segment_count=len(translated),
            duration_sec=duration,
            message="ok" if qc_report else "no qc issues",
        )
        report.write(out)
        return PipelineResult(srt_path, master, qc_report, translated, report)
    except Exception as exc:  # noqa: BLE001
        # Scrub the message so a leaked credential cannot end up in the
        # saved run report.
        safe_message = Secrets.redact_string(str(exc), secrets)
        report.finish(status=STATUS_FAILED, message=safe_message)
        report.write(out)
        raise
