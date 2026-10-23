# SPDX-License-Identifier: AGPL-3.0-or-later
"""English Gradio user interface with three tabs: Transcribe / Settings / About.

Keys are kept in the browser session and forwarded per request. They are
never written to disk or echoed in the UI.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import gradio as gr

from .batch import discover_videos
from .ffmpeg_check import status_message as ffmpeg_status
from .pipeline import run_pipeline
from .secrets import from_mapping
from .translate_providers import check_provider, list_provider_names

SUPPORTED_LANGUAGES = [
    "Auto-detect", "English", "French", "Spanish", "German", "Italian",
    "Portuguese", "Dutch", "Japanese", "Chinese", "Korean", "Russian",
]
SENSITIVITY = ["conservative", "balanced", "aggressive"]
MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]
OUTPUT_FORMATS = ["srt", "vtt", "both"]
MODES = ["api", "local"]
ENGINES = ["openai", "deepgram"]
PROVIDERS = ["grok", "deepseek", "gemini", "ollama", "openai"]


def _resolve_inputs(paths) -> list[Path]:
    """Normalise a Gradio file/multi-input into a list of Paths."""
    if not paths:
        return []
    if isinstance(paths, (str, Path)):
        paths = [paths]
    resolved: list[Path] = []
    for item in paths:
        path = Path(str(getattr(item, "name", item)))
        if path.is_dir():
            resolved.extend(discover_videos(path))
        elif path.exists():
            resolved.append(path)
    return resolved


def _collect_secrets(
    openai_key: str,
    deepgram_key: str,
    grok_key: str,
    deepseek_key: str,
    gemini_key: str,
    hf_token: str,
    ollama_base_url: str,
):
    return from_mapping(
        {
            "OPENAI_API_KEY": openai_key,
            "DEEPGRAM_API_KEY": deepgram_key,
            "XAI_API_KEY": grok_key,
            "DEEPSEEK_API_KEY": deepseek_key,
            "GEMINI_API_KEY": gemini_key,
            "HF_TOKEN": hf_token,
            "OLLAMA_BASE_URL": ollama_base_url,
        }
    )


def _test_keys(
    openai_key: str,
    deepgram_key: str,
    grok_key: str,
    deepseek_key: str,
    gemini_key: str,
    hf_token: str,
    ollama_base_url: str,
) -> str:
    secrets = _collect_secrets(
        openai_key, deepgram_key, grok_key, deepseek_key, gemini_key, hf_token, ollama_base_url
    )
    lines: list[str] = []
    for label, name in (
        ("OpenAI (Whisper + translation)", "openai"),
        ("Deepgram (Nova-2 transcription)", "deepgram"),
        ("xAI / Grok (translation)", "grok"),
        ("DeepSeek (translation)", "deepseek"),
        ("Google Gemini (translation)", "gemini"),
        ("Ollama (local translation)", "ollama"),
    ):
        if name == "deepgram":
            key_value = deepgram_key
        elif name == "ollama":
            key_value = ollama_base_url or ""
        else:
            key_value = {
                "openai": openai_key,
                "grok": grok_key,
                "deepseek": deepseek_key,
                "gemini": gemini_key,
            }[name]
        if not key_value:
            lines.append(f"- {label}: not configured")
            continue
        try:
            ok, msg = check_provider(name, secrets)
        except Exception as exc:  # noqa: BLE001 - we never echo the key
            ok, msg = False, f"Test failed: {exc.__class__.__name__}"
        marker = "OK" if ok else "Invalid"
        lines.append(f"{marker}: {label} — {msg}")
    if hf_token:
        lines.append("OK: Hugging Face token present (used by local faster-whisper only).")
    else:
        lines.append("- Hugging Face token: not configured (optional, local mode only).")
    return "\n".join(lines)


def _run(
    inputs,
    mode: str,
    engine: str,
    sensitivity: str,
    model_size: str,
    source_language: str,
    translate: bool,
    target_language: str,
    provider: str,
    output_format: str,
    glossary: str,
    ensemble: bool,
    openai_key: str,
    deepgram_key: str,
    grok_key: str,
    deepseek_key: str,
    gemini_key: str,
    hf_token: str,
    ollama_base_url: str,
    *,
    progress: gr.Progress = gr.Progress(),
):
    videos = _resolve_inputs(inputs)
    if not videos:
        raise gr.Error("Please add at least one video or audio file, or pick a folder.")

    ffmpeg_ok, ffmpeg_msg = ffmpeg_status()
    if not ffmpeg_ok:
        raise gr.Error(
            ffmpeg_msg
            + " | Tip: install FFmpeg (https://ffmpeg.org) or drop the binaries into "
            "the `_ffmpeg_embedded` folder before retrying."
        )

    if mode == "api" and not openai_key and not deepgram_key and engine == "deepgram":
        raise gr.Error(
            "Deepgram API key is missing. Open the Settings tab, paste your key, "
            "and press 'Test keys' to verify before re-running."
        )
    if mode == "api" and not openai_key and engine == "openai":
        raise gr.Error(
            "OpenAI API key is missing. Open the Settings tab, paste your key, "
            "and press 'Test keys' to verify before re-running."
        )
    if translate and provider and provider != "ollama":
        env_key = {"grok": grok_key, "deepseek": deepseek_key, "gemini": gemini_key, "openai": openai_key}.get(provider, "")
        if not env_key:
            raise gr.Error(
                f"{provider.title()} API key is required for translation. "
                "Open the Settings tab and paste your key."
            )

    secrets = _collect_secrets(
        openai_key, deepgram_key, grok_key, deepseek_key, gemini_key, hf_token, ollama_base_url
    )

    out_dir = Path(tempfile.mkdtemp(prefix="subtitler-ui-"))
    rows: list[list[str]] = []
    downloads: list[str] = []
    previews: list[str] = []

    total = len(videos)
    for index, video in enumerate(videos, start=1):
        progress((index - 1) / total, desc=f"Transcribing {video.name} ({index}/{total})")
        per_dir = out_dir / video.stem
        per_dir.mkdir(parents=True, exist_ok=True)
        try:
            result = run_pipeline(
                video,
                engine_name=engine,
                source_language=source_language if source_language != "Auto-detect" else None,
                target_language=target_language,
                glossary=glossary or "",
                output_dir=per_dir,
                mode=mode,
                sensitivity=sensitivity,
                model_size=model_size,
                output_format=output_format,
                provider=provider if translate else None,
                ensemble=ensemble,
                secrets=secrets,
            )
            downloads.append(str(result.srt_path))
            rows.append([video.name, "done", str(result.srt_path.name), str(result.report.segment_count)])
            if not previews:
                try:
                    previews.append(result.srt_path.read_text(encoding="utf-8")[:4000])
                except OSError:
                    previews.append("(preview unavailable)")
        except Exception as exc:  # noqa: BLE001 - we scrub keys via Secrets
            safe = secrets.redact_string(str(exc), secrets)
            rows.append([video.name, "failed", safe[:120], "0"])

    progress(1.0, desc="Done")
    summary = f"Processed {total} file(s). Outputs saved under {out_dir}."
    return rows, downloads, "\n".join(previews) or "(no preview yet)", summary


def build_ui() -> gr.Blocks:
    providers = list_provider_names() or PROVIDERS
    ffmpeg_ok, ffmpeg_msg = ffmpeg_status()
    theme = gr.themes.Soft(primary_hue="indigo", secondary_hue="slate")

    with gr.Blocks(title="Subtitler", theme=theme) as demo:
        # Key/secret input components — created once at the top so every
        # tab/event handler can reference the same objects (Gradio 6 does
        # not resolve string names against sibling components).
        openai_key = gr.Textbox(visible=False, label="OpenAI API key", type="password")
        deepgram_key = gr.Textbox(visible=False, label="Deepgram API key", type="password")
        grok_key = gr.Textbox(visible=False, label="xAI / Grok API key", type="password")
        deepseek_key = gr.Textbox(visible=False, label="DeepSeek API key", type="password")
        gemini_key = gr.Textbox(visible=False, label="Gemini API key", type="password")
        hf_token = gr.Textbox(visible=False, label="Hugging Face token (local mode)", type="password")
        ollama_base_url = gr.Textbox(visible=False, label="Ollama base URL")

        gr.Markdown(
            "# Subtitler\n"
            "Bring-your-own-keys desktop app for transcribing and translating video/audio. "
            "Keys stay in your browser and are sent only with the current request.\n\n"
            f"**FFmpeg status:** {ffmpeg_msg}"
        )
        if not ffmpeg_ok:
            gr.Markdown(
                "> **FFmpeg missing.** Transcription will fail until FFmpeg "
                "(+ ffprobe) is installed or dropped into `_ffmpeg_embedded/`. "
                "[Download FFmpeg](https://ffmpeg.org)."
            )

        with gr.Tabs():
            # ------------------------- Transcribe -------------------------
            with gr.Tab("Transcribe"):
                gr.Markdown(
                    "Drop one or more video/audio files (or a folder), pick a mode, and "
                    "press **Run**. Translation is optional. Outputs are downloaded per file."
                )
                with gr.Row():
                    inputs = gr.File(
                        label="Video / audio files or folder",
                        file_count="multiple",
                        type="filepath",
                    )
                with gr.Row():
                    mode = gr.Radio(MODES, value="api", label="Mode")
                    engine = gr.Radio(ENGINES, value="openai", label="Engine (API mode)")
                with gr.Row():
                    source = gr.Dropdown(
                        SUPPORTED_LANGUAGES, value="Auto-detect", label="Source language"
                    )
                    target = gr.Dropdown(
                        SUPPORTED_LANGUAGES, value="French", label="Target language (translation)"
                    )
                with gr.Row():
                    sensitivity = gr.Dropdown(SENSITIVITY, value="balanced", label="Sensitivity")
                    model_size = gr.Dropdown(MODEL_SIZES, value="large-v3", label="Local model size")
                with gr.Row():
                    translate = gr.Checkbox(value=False, label="Translate subtitles")
                    provider = gr.Dropdown(providers, value=providers[0], label="Translation provider")
                with gr.Row():
                    output_format = gr.Radio(OUTPUT_FORMATS, value="srt", label="Output format")
                    ensemble = gr.Checkbox(value=False, label="Ensemble (two transcription passes)")
                glossary = gr.Textbox(
                    label="Glossary (optional, comma-separated term=translation pairs)",
                    placeholder="e.g. Sora=空, Taki=滝",
                )
                run_btn = gr.Button("Run", variant="primary")
                with gr.Row():
                    results = gr.Dataframe(
                        headers=["File", "Status", "Subtitle", "Segments"],
                        label="Per-file results",
                        interactive=False,
                    )
                with gr.Row():
                    downloads = gr.File(label="Download subtitles", file_count="multiple")
                gr.Textbox(label="Live log", lines=8, interactive=False)
                preview = gr.Textbox(label="SRT preview (first file)", lines=12, interactive=False)
                summary = gr.Markdown()

                run_btn.click(
                    _run,
                    inputs=[
                        inputs, mode, engine, sensitivity, model_size,
                        source, translate, target, provider, output_format,
                        glossary, ensemble,
                        openai_key, deepgram_key, grok_key, deepseek_key,
                        gemini_key, hf_token, ollama_base_url,
                    ],
                    outputs=[results, downloads, preview, summary],
                )

            # ------------------------- Settings --------------------------
            with gr.Tab("Settings / API keys"):
                gr.Markdown(
                    "Type your keys below. They live in the browser only and are "
                    "sent with the next request. Press **Test keys** to verify each "
                    "provider with a real lightweight call.\n\n"
                    "Keys are never written to disk, logged, or echoed back."
                )
                with gr.Row():
                    openai_key = gr.Textbox(label="OpenAI API key", type="password")
                    deepgram_key = gr.Textbox(label="Deepgram API key", type="password")
                with gr.Row():
                    grok_key = gr.Textbox(label="xAI / Grok API key", type="password")
                    deepseek_key = gr.Textbox(label="DeepSeek API key", type="password")
                with gr.Row():
                    gemini_key = gr.Textbox(label="Gemini API key", type="password")
                    hf_token = gr.Textbox(label="Hugging Face token (local mode)", type="password")
                ollama_base_url = gr.Textbox(
                    label="Ollama base URL (optional, e.g. http://localhost:11434/v1)"
                )
                test_btn = gr.Button("Test keys", variant="secondary")
                test_status = gr.Textbox(label="Validation results", lines=10, interactive=False)
                test_btn.click(
                    _test_keys,
                    inputs=[
                        openai_key, deepgram_key, grok_key, deepseek_key,
                        gemini_key, hf_token, ollama_base_url,
                    ],
                    outputs=test_status,
                )

            # --------------------------- About ----------------------------
            with gr.Tab("About"):
                gr.Markdown(
                    "## Subtitler\n\n"
                    "AGPL-3.0-or-later. See the project [README](https://github.com/) "
                    "for installation, batch usage, and privacy notes.\n\n"
                    "- **FFmpeg** is required for audio extraction and probing.\n"
                    "- All API keys are **bring-your-own**: nothing is bundled or logged.\n"
                    "- Translation providers are pluggable (Grok, DeepSeek, Gemini, "
                    "Ollama, OpenAI).\n"
                )

    return demo


def main() -> None:
    demo = build_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)


if __name__ == "__main__":
    main()
