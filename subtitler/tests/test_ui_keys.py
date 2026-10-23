# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for the Settings tab: real per-provider validation calls."""
from __future__ import annotations

from unittest import mock

from app.secrets import from_mapping
from app.translate_providers import check_provider


def _fake_response(status: int = 200):
    resp = mock.MagicMock()
    resp.status = status
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


def test_test_provider_marks_ok_on_2xx():
    secrets = from_mapping({"OPENAI_API_KEY": "sk-valid-look-1234567890ABCDEF"})
    with mock.patch("urllib.request.urlopen", return_value=_fake_response(200)):
        ok, msg = check_provider("openai", secrets)
    assert ok is True
    assert "OK" in msg
    assert "sk-valid" not in msg  # key never echoed


def test_test_provider_marks_invalid_on_401():
    secrets = from_mapping({"OPENAI_API_KEY": "sk-bad-look-1234567890ABCDEF"})
    import urllib.error

    with mock.patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError("url", 401, "Unauthorized", {}, None),
    ):
        ok, msg = check_provider("openai", secrets)
    assert ok is False
    assert "Invalid" in msg or "rejected" in msg


def test_test_provider_handles_network_error():
    secrets = from_mapping({"OPENAI_API_KEY": "sk-network-look-1234567890ABCDEF"})
    import urllib.error

    with mock.patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("dns down"),
    ):
        ok, msg = check_provider("openai", secrets)
    assert ok is False
    assert "Network" in msg or "error" in msg.lower()


def test_test_provider_reports_not_configured():
    secrets = from_mapping({})
    ok, msg = check_provider("openai", secrets)
    assert ok is False
    assert "Not configured" in msg


def test_test_provider_uses_friendly_label_not_technical():
    """The user-facing message should never be ``Configured: []``."""
    secrets = from_mapping({})
    ok, msg = check_provider("grok", secrets)
    assert "Configured" not in msg
    assert "[]" not in msg


def test_test_provider_handles_ollama_unreachable():
    secrets = from_mapping({"OLLAMA_BASE_URL": "http://localhost:1/v1"})
    ok, msg = check_provider("ollama", secrets)
    assert ok is False
    assert "Ollama" in msg or "unreachable" in msg.lower() or "error" in msg.lower()


def test_test_provider_handles_ollama_reachable(tmp_path):
    import socket

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    try:
        secrets = from_mapping({"OLLAMA_BASE_URL": f"http://127.0.0.1:{port}/v1"})
        ok, msg = check_provider("ollama", secrets)
    finally:
        server.close()
    assert ok is True
    assert "OK" in msg or "reachable" in msg.lower()
