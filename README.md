# subtitler

An open-source subtitle pipeline for turning video into readable, translated SRT subtitles with audio mastering and quality control.

## Features

- FFprobe track inspection and deterministic WAV extraction (48 kHz, 24-bit PCM).
- Speech recognition through OpenAI Whisper or Deepgram Nova-2, including diarization where supported.
- Automatic chunking for Whisper inputs larger than 25 MB.
- Adapted xAI Grok translation with glossary and previous-line context.
- Netflix-style subtitle QC: line length, reading speed, duration, gaps, and line balancing.
- Gradio interface and a Python API suitable for automation.
- No uploads or persistent storage by default.

## Install

### Local virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.ui
```

Open the printed Gradio URL, normally `http://127.0.0.1:7860`.

### Docker

```bash
docker build -t subtitler .
docker run --rm -p 7860:7860 --env-file .env subtitler
```

FFmpeg is required locally and is included in the Docker image.

## API keys

| Variable | Provider | Used for |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI | Whisper transcription |
| `DEEPGRAM_API_KEY` | Deepgram | Nova-2 transcription |
| `XAI_API_KEY` | xAI | Grok translation |
| `GROK_MODEL` | xAI | Model name; defaults to `grok-4` |
| `HF_TOKEN` | Hugging Face | Reserved for future separation models |

Copy `.env.example` to `.env` and add your own keys. Never commit secrets.

## Usage

The UI accepts a video file, an engine, source and target languages, and an optional glossary. It writes an SRT file, a mastered WAV file, and a JSON QC report to a temporary working directory. For Python use:

```python
from app.pipeline import run_pipeline

result = run_pipeline("input.mp4", engine_name="openai", target_language="French")
print(result.srt_path, result.qc_report)
```

## Project structure

```text
app/                 Pipeline package and Gradio UI
tests/               Offline unit tests
docs/                Additional project documentation
.github/             CI and contribution templates
```

## Roadmap

- [ ] Demucs separation
- [ ] Per-segment language detection
- [ ] Agentic character voice profiles
- [ ] Anonymous community translation platform
- [ ] TTML export

## Responsible use

This project does not distribute videos. You are responsible for having the rights and permissions needed for every file and API submission. Use it only for adults-only legal, consensual content; never use it for minors or non-consensual content. The software is provided without warranty, and third-party providers may have their own terms and retention policies.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md), run `ruff check .` and `pytest`, and keep changes focused. By contributing, you agree to the repository's code of conduct.

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE).
