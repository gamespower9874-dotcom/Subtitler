# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pluggable translation providers built on the OpenAI-compatible SDK.

``check_provider`` (formerly ``test_provider``) now performs a real, lightweight validation call for
each provider (it never logs or echoes the key).
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI

from .config import settings
from .secrets import Secrets


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    api_key: str | None
    base_url: str
    model: str


def discover_providers(secrets: Secrets | None = None) -> dict[str, ProviderSpec]:
    secrets = secrets or Secrets()
    providers: dict[str, ProviderSpec] = {}

    def _env(name: str) -> str | None:
        value = secrets.get(name)
        return value or None

    if (key := _env("XAI_API_KEY")):
        providers["grok"] = ProviderSpec("grok", key, "https://api.x.ai/v1", settings.grok_model)
    if (key := _env("DEEPSEEK_API_KEY")):
        providers["deepseek"] = ProviderSpec("deepseek", key, "https://api.deepseek.com/v1", settings.deepseek_model)
    if (key := _env("GEMINI_API_KEY")):
        providers["gemini"] = ProviderSpec("gemini", key, "https://generativelanguage.googleapis.com/v1beta/openai", settings.gemini_model)
    base = _env("OLLAMA_BASE_URL") or settings.ollama_base_url
    providers["ollama"] = ProviderSpec("ollama", _env("OLLAMA_API_KEY") or "ollama", base, settings.ollama_model)
    if (key := _env("OPENAI_API_KEY")):
        providers["openai"] = ProviderSpec("openai", key, "https://api.openai.com/v1", "gpt-4o-mini")
    return providers


class TranslationProvider(Protocol):
    name: str

    def translate(
        self,
        segments: list[dict],
        target_language: str,
        glossary: str,
        client: OpenAI | None = None,
    ) -> list[str]: ...


class OpenAICompatibleProvider:
    spec: ProviderSpec

    def __init__(self, spec: ProviderSpec) -> None:
        self.spec = spec
        self.name = spec.name
        self._client: OpenAI | None = None

    def _client_for(self, client: OpenAI | None) -> OpenAI:
        if client is not None:
            return client
        if self._client is None:
            self._client = OpenAI(api_key=self.spec.api_key, base_url=self.spec.base_url)
        return self._client

    def translate(
        self,
        segments: list[dict],
        target_language: str,
        glossary: str,
        client: OpenAI | None = None,
    ) -> list[str]:
        if not segments:
            return []
        client_obj = self._client_for(client)
        out: list[str] = []
        for start in range(0, len(segments), 20):
            batch = segments[start : start + 20]
            try:
                response = client_obj.chat.completions.create(
                    model=self.spec.model,
                    messages=[
                        {"role": "system", "content": "You are a subtitle translator. Output JSON only."},
                        {"role": "user", "content": f"Translate into {target_language}. Source: {json.dumps(batch, ensure_ascii=False)}"},
                    ],
                    temperature=0.2,
                )
                data = json.loads(response.choices[0].message.content)
                for item in data:
                    out.append(str(item.get("text", "")))
            except Exception:
                out.extend(item.get("text", "") for item in batch)
        return out


def build_provider(name: str, secrets: Secrets | None = None) -> OpenAICompatibleProvider | None:
    if not name:
        return None
    providers = discover_providers(secrets)
    key = name.strip().lower()
    if key not in providers:
        return None
    return OpenAICompatibleProvider(providers[key])


def list_provider_names(secrets: Secrets | None = None) -> list[str]:
    return sorted(discover_providers(secrets).keys())


# Map provider name -> tiny endpoint used for a real validation call.
_PROBE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1/models",
    "grok": "https://api.x.ai/v1/models",
    "deepseek": "https://api.deepseek.com/v1/models",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/v1/models",
    "ollama": "__local__",  # special: TCP probe
}


def _probe_http(url: str, key: str) -> tuple[bool, str]:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:  # nosec - URL is hard-coded
            if 200 <= response.status < 300:
                return True, "OK (live API call succeeded)"
            return False, f"Invalid key (HTTP {response.status})"
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return False, "Invalid key (rejected by provider)"
        return False, f"Provider error (HTTP {exc.code})"
    except (urllib.error.URLError, socket.timeout, OSError) as exc:
        return False, f"Network error: {exc.__class__.__name__}"


def _probe_local(url: str) -> tuple[bool, str]:
    """TCP probe of an Ollama base URL."""
    try:
        without_scheme = url.split("://", 1)[1]
        host_port = without_scheme.split("/", 1)[0]
        host, _, port = host_port.partition(":")
        port = int(port or "11434")
    except (ValueError, IndexError):
        return False, "Ollama URL not configured"
    try:
        with socket.create_connection((host, port), timeout=4):
            return True, f"OK (reachable at {host}:{port})"
    except (socket.timeout, OSError) as exc:
        return False, f"Ollama unreachable ({exc.strerror or exc.__class__.__name__})"


def check_provider(name: str, secrets: Secrets | None = None) -> tuple[bool, str]:
    """Run a real, lightweight validation against the provider.

    Returns ``(ok, human_message)``. The key is never echoed back.
    """
    secrets = secrets or Secrets()
    spec = discover_providers(secrets).get(name.lower())
    if spec is None or not spec.api_key:
        if name.lower() == "ollama":
            ok, msg = _probe_local(settings.ollama_base_url)
            return ok, msg if ok else f"Not configured: {msg}"
        return False, "Not configured (no key entered)"
    key = spec.api_key or ""
    url = _PROBE_URLS.get(name.lower())
    if url == "__local__":
        return _probe_local(spec.base_url)
    if not url:
        return False, "No probe endpoint known for this provider"
    return _probe_http(url, key)


__all__ = [
    "ProviderSpec",
    "OpenAICompatibleProvider",
    "build_provider",
    "discover_providers",
    "list_provider_names",
    "check_provider",
]
