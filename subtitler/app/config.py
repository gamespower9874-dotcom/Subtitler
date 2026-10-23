# SPDX-License-Identifier: AGPL-3.0-or-later
"""Environment-backed application configuration.

This module deliberately exposes only **public** configuration knobs
(model names, optional Ollama base URL) via :class:`Settings`. The
:class:`Secrets` container lives in :mod:`app.secrets` so callers can
build a per-request view that takes priority over the environment.

The ``load_dotenv`` call does **not** override values that are already
present in ``os.environ`` — keys a user supplies at request time (or
via CLI flags) therefore win over any value sitting in ``.env``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

from .secrets import Secrets

load_dotenv(override=False)


@dataclass(frozen=True)
class Settings:
    """Non-secret configuration knobs sourced from the environment."""

    raw: dict[str, Any] = field(default_factory=lambda: dict(os.environ))

    def __getattr__(self, item: str) -> Any:
        env_name = item.upper()
        if item in self.raw:
            return self.raw[item]
        if env_name in self.raw:
            return self.raw[env_name]
        return None

    @property
    def grok_model(self) -> str:
        return os.getenv("GROK_MODEL", "grok-4")

    @property
    def deepseek_model(self) -> str:
        return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    @property
    def gemini_model(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    @property
    def ollama_base_url(self) -> str:
        return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    @property
    def ollama_model(self) -> str:
        return os.getenv("OLLAMA_MODEL", "llama3.1")


settings = Settings()


def make_secrets(overrides: dict[str, Any] | None = None) -> Secrets:
    """Factory that builds a :class:`Secrets` from request-supplied overrides."""
    return Secrets({k: v for k, v in (overrides or {}).items() if v})


__all__ = ["Settings", "settings", "make_secrets"]