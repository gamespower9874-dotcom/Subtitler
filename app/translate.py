# SPDX-License-Identifier: AGPL-3.0-or-later
"""Context-aware subtitle translation through xAI's OpenAI-compatible API."""
import json
from openai import OpenAI
from .config import settings


def translate_segments(segments: list[dict], target_language: str = "French", glossary: str = "", client=None) -> list[dict]:
    """Translate in batches, preserving timing and falling back to source text on errors."""
    if not segments:
        return []
    client = client or OpenAI(api_key=settings.xai_api_key, base_url="https://api.x.ai/v1")
    result = [dict(item) for item in segments]
    for start in range(0, len(segments), 20):
        batch = segments[start:start + 20]
        payload = [{"index": i, "text": item.get("text", "")} for i, item in enumerate(batch)]
        context = " ".join(item.get("text", "") for item in segments[max(0, start - 3):start])
        prompt = f"Translate into {target_language}. Adapt naturally, do not translate literally. Return strict JSON array of objects with index and text. Glossary: {glossary or 'none'}. Previous lines: {context or 'none'}. Source: {json.dumps(payload, ensure_ascii=False)}"
        try:
            response = client.chat.completions.create(model=settings.grok_model, messages=[{"role": "system", "content": "You are a subtitle translator. Output JSON only."}, {"role": "user", "content": prompt}], temperature=0.2)
            data = json.loads(response.choices[0].message.content)
            translated = {int(item["index"]): str(item["text"]) for item in data}
            for i, item in enumerate(batch):
                result[start + i]["text"] = translated.get(i, item.get("text", ""))
        except Exception:
            # Preserve source text when the provider is unavailable or returns invalid JSON.
            continue
    return result
