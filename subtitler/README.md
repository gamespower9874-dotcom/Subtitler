# Subtitler

Subtitler is an open-source (AGPL-3.0-or-later) Python pipeline for
**transcribing** and **translating** video subtitles. It ships with a
Gradio web UI, a command-line interface, and ready-to-use PyInstaller
recipes for Windows.

## Features

* **API mode** using OpenAI Whisper or Deepgram Nova-2.
* **Local mode** using [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
  with built-in Silero VAD and three sensitivity presets
  (`conservative`, `balanced`, `aggressive`).
* **Japanese post-processing** (`app/jp_postprocess.py`) that filters
  Whisper hallucinations (consecutive repeats, n-gram loops,
  no-speech lines, music cues, kana-only noise), merges short segments
  on trailing particles (ね/よ/わ/か/な/ぞ/ぜ) and clamps / dedupes
  timings.
* **Ensemble mode** that combines two transcription passes and fills
  the gaps in the primary output with the secondary pass.
* **Run reports** (`app/run_report.py`) emitted as `run.json` plus a
  one-line console summary.
* **Batch discovery** (`app/batch.py`) for folders with `--recursive`
  and `--skip-existing` flags.
* **Pluggable translation providers** (`app/translate_providers.py`)
  using the OpenAI-compatible SDK with a configurable `base_url`:
  Grok (xAI), DeepSeek, Gemini, Ollama (local) and OpenAI.
* **VTT output** alongside SRT (`--output-format both`).
* **QC rules** (`app/qc.py`) with CPS / duration / gap checks.

## Quick start

```bash
pip install -r requirements.txt
pip install -r requirements-local.txt  # optional local extras
cp .env.example .env  # then fill in the API keys you need
```

### Gradio UI

```bash
python -m app.ui
```

### CLI

```bash
python -m app.cli path/to/video.mp4 \
    --mode local --sensitivity balanced \
    --translate --provider grok --target-lang French \
    --output-format both
```

## Bring your own API keys

Subtitler does **not** ship with API keys and never will. You supply
them yourself, and they stay on your machine.

### Where keys go

| Where | How |
|---|---|
| **Web UI** | Open the **Settings — API keys (optional)** accordion. Each provider has its own field with `type="password"`; values are held in the browser session and sent along with the next transcription request. Leave a field blank to fall back to the matching env var. |
| **`.env` file** | Copy `.env.example` to `.env` and fill the placeholders. `.env` is gitignored. The keys are loaded only when the Python process starts. |
| **CLI flags** | `--api-key-openai`, `--api-key-deepgram`, `--api-key-grok`/`--api-key-xai`, `--api-key-deepseek`, `--api-key-gemini`, `--api-key-hf`, `--ollama-base-url`. These override `.env` for that single invocation. |

A small **Test translation keys** button in the Settings panel runs an
offline presence check for each provider without making a network call,
so you can confirm the key was typed correctly.

### Priority

For each provider, the backend tries, in order:

1. The value typed into the UI for **this request** (highest priority).
2. The value passed via CLI flag (`--api-key-<provider>`).
3. The value in the local `.env` file or process environment.

Per-request values never outlive the request.

### Privacy

* Keys are **never** written to disk by the application.
* Keys are **never** logged; the run report (`run.json`), QC output,
  exception messages, and the console summary are scrubbed through
  `app.secrets.Secrets.redact_string` before they are saved or printed.
* Keys are **never** included in the per-request error response back to
  the browser.
* The Gradio backend is local (`127.0.0.1` in `launcher.py`,
  `0.0.0.0` only when explicitly launched via `python -m app.ui`).
* When you choose an external provider (OpenAI, Deepgram, xAI, …), the
  audio and translated text are sent to that provider under *their*
  retention policy — Subtitler has no visibility into that side-channel.
* **Never commit `.env`**. `.env` is in `.gitignore`; only `.env.example`
  with empty placeholders is tracked.

## UI

Subtitler ships with a Gradio web UI (`app/ui.py`) exposing three tabs:

* **Transcribe** — drop one or more video files (or a folder), pick the
  transcription mode (`api` for OpenAI Whisper / Deepgram Nova-2, or
  `local` for `faster-whisper` + Silero VAD), the model size, the
  sensitivity preset, the output format (SRT / VTT / both) and
  optionally enable translation. The pipeline streams progress and
  finishes by giving you the `.srt` (and `.vtt`) downloads alongside a
  `run.json` report.
* **Settings — API keys (optional)** — `password` text boxes for every
  supported provider (OpenAI, Deepgram, xAI / Grok, DeepSeek, Gemini,
  HF token, Ollama base URL). Keys live only in the browser session,
  are forwarded per request, and are never written to disk. The
  **Test keys** button performs a real, lightweight validation call
  for each provider and reports OK / Invalid without ever echoing the
  key back.
* **About** — short blurb on FFmpeg requirements, the bring-your-own
  keys policy and the pluggable translation providers.

Launch the UI from the project root:

```bash
python -m app.ui          # default: 127.0.0.1:7860
# or, on Windows / frozen builds:
python launcher.py
```

Both code paths start Gradio on `127.0.0.1` (loopback only) so the
backend never accidentally exposes your keys to the network. The
Gradio status banner reports whether FFmpeg / FFprobe are available.

## Inspiration

The local Japanese workflow was inspired by ideas from
[WhisperJAV](https://github.com/Soothsilver/WhisperJAV) (MIT). All code
in this repository is written from scratch and released under
AGPL-3.0-or-later; no code from WhisperJAV has been copied.

## License

AGPL-3.0-or-later. See `LICENSE` for the full text.
