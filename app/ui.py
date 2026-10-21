# SPDX-License-Identifier: AGPL-3.0-or-later
"""English Gradio user interface."""
import json
import tempfile
from pathlib import Path
import gradio as gr
from .pipeline import run_pipeline

def process(video, engine, source_language, target_language, glossary):
    if not video:
        raise gr.Error("Please provide a video file.")
    result = run_pipeline(video, engine, source_language or None, target_language, glossary)
    report = Path(tempfile.mkdtemp(prefix="subtitler-ui-")) / "qc_report.json"
    report.write_text(json.dumps(result.qc_report, indent=2), encoding="utf-8")
    return str(result.srt_path), str(result.master_wav_path), str(report)

def build_ui():
    with gr.Blocks(title="subtitler") as demo:
        gr.Markdown("# subtitler\nSubtitle transcription, translation, and quality control")
        video = gr.File(label="Video", file_types=["video"])
        with gr.Row():
            engine = gr.Dropdown(["openai", "deepgram"], value="openai", label="Transcription engine")
            source = gr.Textbox(label="Source language (optional)")
            target = gr.Textbox(value="French", label="Target language")
        glossary = gr.Textbox(label="Glossary (optional)", lines=3)
        button = gr.Button("Create subtitles", variant="primary")
        srt = gr.File(label="SRT subtitles")
        wav = gr.File(label="Master WAV")
        qc = gr.File(label="QC report")
        button.click(process, [video, engine, source, target, glossary], [srt, wav, qc])
    return demo

if __name__ == "__main__":
    build_ui().launch(server_name="0.0.0.0", server_port=7860)
