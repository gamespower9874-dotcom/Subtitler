# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-request API-key handling.

Keys are never bundled with the project. They are supplied in three ways,
in increasing priority:

1. Environment variables (``OPENAI_API_KEY`` etc.) loaded from a local
   ``.env`` file the user creates themselves (the repo only ships
   ``.env.example`` with empty placeholders).
2. CLI flags such as ``--api-key-openai`` (or ``--ollama-base-url``).
3. Fields typed into the web UI on a per-request basis. These are kept
   in the user's browser only and are sent to the backend over the
   Gradio request. The backend uses them for that single request and
   does not persist, log, or echo them anywhere.

This module deliberately avoids ``__repr__``/``__str__`` that would leak
key material, exposes a ``redact_string`` helper so any text destined
for logs, run reports, or UI surfaces is scrubbed, and never writes the
overrides to disk.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Mapping

# Canonical env-var names for the supported providers. Model names and
# the optional Ollama base URL live in the same env namespace but are
# not treated as secrets (they are public endpoints / model ids).
_KEY_ENV_NAMES: frozenset[str] = frozenset(
    {
        "OPENAI_API_KEY",
        "DEEPGRAM_API_KEY",
        "XAI_API_KEY",
        "DEEPSEEK_API_KEY",
        "GEMINI_API_KEY",
        "HF_TOKEN",
        "OLLAMA_API_KEY",
    }
)


@dataclass
class Secrets:
    """Container for API keys supplied for one pipeline run.

    ``overrides`` is the raw key map as supplied by the caller (request
    payload, CLI flags, or any other source). Empty strings and ``None``
    values are dropped on construction so a missing key stays missing.
    """

    overrides: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        cleaned: dict[str, str] = {}
        for key, value in self.overrides.items():
            if value is None:
                continue
            text = str(value).strip()
            if not text:
                continue
            cleaned[key] = text
        self.overrides = cleaned

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Secrets(keys={sorted(self.overrides)!r})"

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return self.__repr__()

    # --- Resolution --------------------------------------------------

    def get(self, name: str) -> str | None:
        """Return the key for ``name`` (case-insensitive).

        Priority: explicit override > environment variable > ``None``.
        """
        env_name = name.upper()
        if env_name in self.overrides:
            return self.overrides[env_name]
        if name in self.overrides:
            return self.overrides[name]
        env_value = os.getenv(env_name)
        return env_value or None

    def has(self, name: str) -> bool:
        return bool(self.get(name))

    # --- Safe serialisation -----------------------------------------

    def to_redacted_dict(self) -> dict[str, str]:
        """Return a copy of overrides with each value masked."""
        return {name: _redact(value) for name, value in self.overrides.items()}

    @staticmethod
    def redact_string(text: str, *sources: "Secrets | Mapping[str, Any] | None") -> str:
        """Replace every secret value found in ``text`` with ``***``.

        Each positional argument may be a :class:`Secrets` instance or a
        plain mapping of key strings. Only the values are scrubbed — keys
        are public identifiers and stay readable.
        """
        if not text:
            return text
        collected: list[str] = []
        for source in sources:
            if source is None:
                continue
            if isinstance(source, Secrets):
                collected.extend(source.overrides.values())
            elif isinstance(source, Mapping):
                collected.extend(str(v) for v in source.values() if v)
        # Also redact anything from the environment that looks like a key,
        # so leaked env values never make it into a run report.
        for env_name in _KEY_ENV_NAMES:
            env_value = os.getenv(env_name)
            if env_value:
                collected.append(env_value)
        for value in collected:
            if not value or len(value) < 6:
                # Skip ultra-short values to avoid masking harmless tokens.
                continue
            text = text.replace(value, _redact(value))
        return text


def _redact(value: str) -> str:
    """Return a masked form of ``value`` safe to print or store."""
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    head = value[:4]
    tail = value[-4:]
    return f"{head}…{tail}"


def from_mapping(data: Mapping[str, Any] | None) -> Secrets:
    """Build a :class:`Secrets` from an arbitrary mapping.

    Drops known ``key`` / ``api_key`` style entries coming from the UI
    while tolerating extra unknown keys. The intent is that an unknown
    key in the payload does not silently become a credential.
    """
    if not data:
        return Secrets()
    candidates: dict[str, str] = {}
    for raw_key, raw_value in data.items():
        if raw_value is None:
            continue
        key = str(raw_key).strip()
        if not key:
            continue
        # Accept the canonical env-var names and common aliases from
        # the Gradio form (e.g. ``openai_key``).
        alias = _KEY_ALIASES.get(key.lower())
        env_name = alias or key.upper()
        if env_name in _KEY_ENV_NAMES or env_name == "OLLAMA_BASE_URL":
            text = str(raw_value).strip()
            if text:
                candidates[env_name] = text
    return Secrets(candidates)


# Aliases used by the Gradio Settings form so the front-end can use
# friendly names without the user having to memorise env-var casing.
_KEY_ALIASES: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "openai_key": "OPENAI_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "deepgram": "DEEPGRAM_API_KEY",
    "deepgram_key": "DEEPGRAM_API_KEY",
    "deepgram_api_key": "DEEPGRAM_API_KEY",
    "grok": "XAI_API_KEY",
    "xai": "XAI_API_KEY",
    "xai_key": "XAI_API_KEY",
    "xai_api_key": "XAI_API_KEY",
    "grok_key": "XAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "deepseek_key": "DEEPSEEK_API_KEY",
    "deepseek_api_key": "DEEPSEEK_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "gemini_key": "GEMINI_API_KEY",
    "gemini_api_key": "GEMINI_API_KEY",
    "hf": "HF_TOKEN",
    "hf_token": "HF_TOKEN",
    "ollama_key": "OLLAMA_API_KEY",
    "ollama_api_key": "OLLAMA_API_KEY",
    "ollama_base_url": "OLLAMA_BASE_URL",
}


__all__ = ["Secrets", "from_mapping"]
