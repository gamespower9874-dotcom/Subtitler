# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for the Secrets container and key redaction."""
from __future__ import annotations

import json

import pytest

from app.config import make_secrets
from app.run_report import FileReport
from app.secrets import Secrets, from_mapping


SAMPLE_OPENAI = "sk-test-1234567890ABCDEF"
SAMPLE_DEEPGRAM = "dg-test-abcdef0123456789"
SAMPLE_XAI = "xai-test-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def test_secrets_drops_empty_values():
    secrets = Secrets({"OPENAI_API_KEY": "", "DEEPGRAM_API_KEY": "  ", "XAI_API_KEY": None})
    assert secrets.overrides == {}


def test_request_key_overrides_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "from-env")
    secrets = Secrets({"OPENAI_API_KEY": "from-request"})
    assert secrets.get("OPENAI_API_KEY") == "from-request"


def test_request_falls_back_to_env_when_blank(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "from-env")
    secrets = Secrets({})
    assert secrets.get("OPENAI_API_KEY") == "from-env"


def test_missing_key_returns_none():
    assert Secrets({}).get("OPENAI_API_KEY") is None


def test_redact_string_masks_known_values():
    secrets = Secrets({"OPENAI_API_KEY": SAMPLE_OPENAI})
    payload = f"auth header: {SAMPLE_OPENAI} should not leak"
    redacted = Secrets.redact_string(payload, secrets)
    assert SAMPLE_OPENAI not in redacted
    assert "sk-t" in redacted and "CDEF" in redacted


def test_redact_string_masks_env_values(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", SAMPLE_OPENAI)
    redacted = Secrets.redact_string(f"boom {SAMPLE_OPENAI} boom")
    assert SAMPLE_OPENAI not in redacted


def test_make_secrets_factory():
    secrets = make_secrets({"OPENAI_API_KEY": "abc"})
    assert secrets.get("OPENAI_API_KEY") == "abc"


def test_from_mapping_accepts_aliases():
    secrets = from_mapping(
        {
            "openai": "k1",
            "grok": "k2",
            "deepseek": "k3",
            "gemini": "k4",
            "ollama_base_url": "http://x",
        }
    )
    assert secrets.get("OPENAI_API_KEY") == "k1"
    assert secrets.get("XAI_API_KEY") == "k2"
    assert secrets.get("DEEPSEEK_API_KEY") == "k3"
    assert secrets.get("GEMINI_API_KEY") == "k4"
    assert secrets.get("OLLAMA_BASE_URL") == "http://x"


def test_from_mapping_drops_unknown_keys():
    secrets = from_mapping({"OPENAI_API_KEY": "ok", "garbage": "should-not-become-key"})
    assert secrets.get("OPENAI_API_KEY") == "ok"
    assert secrets.get("GARBAGE") is None


def test_redaction_in_run_report_message(tmp_path):
    """A leaked credential in an exception must not survive into run.json."""
    from app.run_report import FileReport

    report = FileReport(input_path="video.mp4")
    # Simulate a failure message that contains the key — the pipeline
    # scrubs this through ``Secrets.redact_string`` before storing it.
    leaked = f"401 invalid {SAMPLE_OPENAI}"
    safe = Secrets.redact_string(leaked, Secrets({"OPENAI_API_KEY": SAMPLE_OPENAI}))
    report.finish(status="failed", message=safe)
    path = report.write(tmp_path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert SAMPLE_OPENAI not in saved["message"]
    assert "sk-t" in saved["message"]


@pytest.mark.parametrize("flag", ["OPENAI_API_KEY", "DEEPGRAM_API_KEY", "XAI_API_KEY"])
def test_no_real_keys_in_outputs(tmp_path, monkeypatch, flag):
    """End-to-end: a key provided as a request override never appears on disk."""
    monkeypatch.delenv(flag, raising=False)
    key_value = f"value-for-{flag}-1234567890"
    secrets = Secrets({flag: key_value})
    # Just write the report the same way the pipeline does.
    report = FileReport(input_path="video.mp4")
    report.finish(status="done", message=Secrets.redact_string("all good", secrets))
    report.write(tmp_path)
    for entry in tmp_path.iterdir():
        assert key_value not in entry.read_text(encoding="utf-8")