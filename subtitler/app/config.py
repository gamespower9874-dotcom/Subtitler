# SPDX-License-Identifier: AGPL-3.0-or-later
"""Environment-backed application configuration."""
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    deepgram_api_key: str | None = os.getenv("DEEPGRAM_API_KEY")
    xai_api_key: str | None = os.getenv("XAI_API_KEY")
    grok_model: str = os.getenv("GROK_MODEL", "grok-4")
    hf_token: str | None = os.getenv("HF_TOKEN")

settings = Settings()
