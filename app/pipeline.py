# SPDX-License-Identifier: AGPL-3.0-or-later
"""High-level subtitle pipeline."""
from dataclasses import dataclass
from pathlib import Path
import json
import tempfile
from .audio import extract_master, make_asr_audio
from .engines.openai_whisper import OpenAIWhisperEngine
from .engines.deepgram_engine import DeepgramEngine
from .qc import check
from .subtitles import to_srt
from .translate import translate_segments

@dataclass
class PipelineResult:
    srt_path: Path
    master_wav_path: Path
    qc_report: list[tuple[int, str]]

def run_pipeline(video: str | Path, engine_name: str = "openai", source_language: str | None = None, target_language: str = "French", glossary: str = "", output_dir: str | Path | None = None) -> PipelineResult:
    out = Path(output_dir or tempfile.mkdtemp(prefix="subtitler-"))
    out.mkdir(parents=True, exist_ok=True)
    master = extract_master(video, out / "master.wav")
    asr = make_asr_audio(master, out / "asr.wav")
    engine = DeepgramEngine() if engine_name.lower() == "deepgram" else OpenAIWhisperEngine()
    segments = engine.transcribe(str(asr), source_language, glossary)
    translated = translate_segments(segments, target_language, glossary)
    report = check(translated)
    srt = to_srt(translated, out / "subtitles.srt")
    (out / "qc_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return PipelineResult(srt, master, report)
