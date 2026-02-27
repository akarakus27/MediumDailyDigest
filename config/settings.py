from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    gmail_credentials: str
    gmail_token: str | None
    gemini_api_key: str | None
    openai_api_key: str | None
    telegram_token: str
    telegram_chat_id: str
    medium_sender_filter: str
    max_articles_per_email: int
    max_preview_chars: int
    processed_store_path: Path

    @property
    def has_ai_provider(self) -> bool:
        return bool(self.gemini_api_key or self.openai_api_key)


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer") from exc


def load_settings() -> Settings:
    gmail_credentials = os.getenv("GMAIL_CREDENTIALS")
    if not gmail_credentials:
        raise ValueError("Missing required environment variable: GMAIL_CREDENTIALS")

    # Validate json early so the app fails fast with clear error.
    json.loads(gmail_credentials)

    telegram_token = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        raise ValueError("Missing required environment variable: TELEGRAM_TOKEN")

    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not telegram_chat_id:
        raise ValueError("Missing required environment variable: TELEGRAM_CHAT_ID")

    return Settings(
        gmail_credentials=gmail_credentials,
        gmail_token=os.getenv("GMAIL_TOKEN"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        telegram_token=telegram_token,
        telegram_chat_id=telegram_chat_id,
        medium_sender_filter=os.getenv("MEDIUM_SENDER_FILTER", "noreply@medium.com"),
        max_articles_per_email=_read_int("MAX_ARTICLES_PER_EMAIL", 5),
        max_preview_chars=_read_int("MAX_PREVIEW_CHARS", 1000),
        processed_store_path=Path(os.getenv("PROCESSED_STORE_PATH", "storage/processed_emails.json")),
    )
