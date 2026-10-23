# SPDX-License-Identifier: AGPL-3.0-or-later
"""Translation entry point. Backward compatible with the existing tests."""
from __future__ import annotations

import json

from openai import OpenAI

from .config import settings
from .secrets import Secrets
from .translate_providers import build_provider


def translate_segments(
    segments: list[dict],
    target_language: str = "French",
    glossary: str = "",
    client: object | None = None,
    provider: str | None = None,
    secrets: Secrets | None = None,
) -> list[dict]:
    """Translate ``segments`` in batches. Preserves timing.

    ``secrets`` is the per-request container built from the UI fields
    (or CLI flags). It takes priority over environment variables so a
    user can override their ``.env`` values without restarting the
    service. No key is ever written to disk, logged, or echoed back.
    """
    if not segments:
        return []
    result = [dict(item) for item in segments]
    secrets = secrets or Secrets()

    chosen = None
    if provider:
        chosen = build_provider(provider, secrets)
    if chosen is not None:
        try:
            texts = chosen.translate(
                segments,
                target_language,
                glossary,
                client=client if isinstance(client, OpenAI) else None,
            )
            for i, text in enumerate(texts):
                result[i]["text"] = text
            return result
        except Exception:
            pass

    # Legacy fallback: hit the xAI endpoint using either the user-supplied
    # key or, if absent, the environment. ``client`` overrides either.
    legacy_key = secrets.get("XAI_API_KEY")
    legacy_client = client or OpenAI(api_key=legacy_key, base_url="https://api.x.ai/v1")
    for start in range(0, len(segments), 20):
        batch = segments[start : start + 20]
        payload = [{"index": i, "text": item.get("text", "")} for i, item in enumerate(batch)]
        context = " ".join(item.get("text", "") for item in segments[max(0, start - 3) : start])
        prompt = (
            f"Translate into {target_language}. Adapt naturally, do not translate literally. "
            f"Return strict JSON array of objects with index and text. "
            f"Glossary: {glossary or 'none'}. Previous lines: {context or 'none'}. "
            f"Source: {json.dumps(payload, ensure_ascii=False)}"
        )
        try:
            response = legacy_client.chat.completions.create(
                model=settings.grok_model,
                messages=[
                    {"role": "system", "content": "You are a subtitle translator. Output JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            data = json.loads(response.choices[0].message.content)
            translated = {int(item["index"]): str(item["text"]) for item in data}
            for i, item in enumerate(batch):
                result[start + i]["text"] = translated.get(i, item.get("text", ""))
        except Exception:
            continue
    return result
