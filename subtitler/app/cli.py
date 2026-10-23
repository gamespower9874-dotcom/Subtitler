# SPDX-License-Identifier: AGPL-3.0-or-later
"""Command-line interface for the subtitler pipeline."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .batch import iter_videos
from .pipeline import run_pipeline
from .run_report import FileReport, summarise
from .secrets import Secrets

# Providers that can be overridden from the CLI in addition to the
# canonical env-var names.
_KEY_FLAGS: dict[str, str] = {
    "--api-key-openai": "OPENAI_API_KEY",
    "--api-key-deepgram": "DEEPGRAM_API_KEY",
    "--api-key-grok": "XAI_API_KEY",
    "--api-key-xai": "XAI_API_KEY",
    "--api-key-deepseek": "DEEPSEEK_API_KEY",
    "--api-key-gemini": "GEMINI_API_KEY",
    "--api-key-hf": "HF_TOKEN",
    "--ollama-base-url": "OLLAMA_BASE_URL",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="subtitler-cli",
        description="Transcribe and translate video subtitles.",
    )
    parser.add_argument("input", nargs="+", help="Video file(s) or folder(s)")
    parser.add_argument("--mode", choices=["api", "local"], default="api", help="Transcription mode")
    parser.add_argument("--sensitivity", choices=["conservative", "balanced", "aggressive"], default="balanced")
    parser.add_argument("--engine", default="openai", help="Engine name for API mode (openai or deepgram)")
    parser.add_argument("--model", default="large-v3", help="Local model size when --mode=local")
    parser.add_argument("--source-lang", default=None, help="Source language code (e.g. ja)")
    parser.add_argument("--translate", action="store_true", help="Enable translation")
    parser.add_argument("--target-lang", default="French", help="Target language")
    parser.add_argument("--output-format", choices=["srt", "vtt", "both"], default="srt")
    parser.add_argument(
        "--provider",
        default=None,
        help="Translation provider (grok, deepseek, gemini, ollama, openai)",
    )
    parser.add_argument("--skip-existing", action="store_true", help="Skip inputs with existing .srt/.vtt")
    parser.add_argument("--recursive", action="store_true", help="Recurse into folders")
    parser.add_argument("--ensemble", action="store_true", help="Combine two transcription passes")
    parser.add_argument("--glossary", default="", help="Optional glossary injected into prompts")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: temp)")

    # --- BYO keys ---------------------------------------------------
    for flag, env_name in _KEY_FLAGS.items():
        parser.add_argument(
            flag,
            dest=env_name.lower(),
            default=None,
            help=(
                f"Override {env_name} for this invocation (value is held in "
                f"memory only, never written to disk or logged)"
            ),
        )
    return parser


def _collect_secrets(args: argparse.Namespace) -> Secrets:
    overrides: dict[str, str] = {}
    for env_name in _KEY_FLAGS.values():
        value = getattr(args, env_name.lower(), None)
        if value:
            overrides[env_name] = str(value)
    return Secrets(overrides)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    inputs = [Path(p) for p in args.input]
    provider = args.provider if args.translate else None
    output_dir = Path(args.output_dir) if args.output_dir else None
    secrets = _collect_secrets(args)

    reports: list[FileReport] = []
    for video in iter_videos(inputs, recursive=args.recursive, skip_existing=args.skip_existing):
        result = run_pipeline(
            video,
            engine_name=args.engine,
            source_language=args.source_lang,
            target_language=args.target_lang,
            glossary=args.glossary,
            output_dir=output_dir,
            mode=args.mode,
            sensitivity=args.sensitivity,
            model_size=args.model,
            output_format=args.output_format,
            provider=provider,
            ensemble=args.ensemble,
            secrets=secrets,
        )
        reports.append(result.report)
        # ``summarise`` is a single line; redact any key that may have been
        # forwarded by a subclass or future message field.
        print(Secrets.redact_string(f"[{result.report.status}] {video} -> {result.srt_path}", secrets))

    print(summarise(reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
