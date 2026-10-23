# SPDX-License-Identifier: AGPL-3.0-or-later
import subprocess
import sys

from app.cli import build_parser, main


def test_help_exits_clean():
    result = subprocess.run(
        [sys.executable, "-m", "app.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "subtitler-cli" in result.stdout


def test_parser_has_expected_flags():
    parser = build_parser()
    args = parser.parse_args(["input.mp4", "--mode", "local", "--translate", "--provider", "grok"])
    assert args.mode == "local"
    assert args.translate is True
    assert args.provider == "grok"


def test_main_with_no_inputs_calls_parser(monkeypatch):
    """Smoke test: ``main`` should call argparse (which exits on missing args)."""
    import pytest
    with pytest.raises(SystemExit):
        main([])
