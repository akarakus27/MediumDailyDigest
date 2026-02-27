from __future__ import annotations

import json
from pathlib import Path

from config.settings import load_settings
from core.router import default_router
from services.ai.summarizer import AISummarizer
from services.gmail.client import GmailClient
from services.gmail.fetcher import GmailFetcher
from services.notifier.telegram import TelegramNotifier


def load_processed_ids(path: Path) -> set[str]:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]\n", encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data)


def save_processed_ids(path: Path, processed_ids: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(processed_ids), indent=2) + "\n", encoding="utf-8")


def main() -> None:
    settings = load_settings()

    gmail_client = GmailClient(settings.gmail_credentials, settings.gmail_token)
    gmail = GmailFetcher(gmail_client)
    router = default_router(
        max_articles=settings.max_articles_per_email,
        max_preview_chars=settings.max_preview_chars,
    )
    summarizer = AISummarizer(
        gemini_api_key=settings.gemini_api_key,
        openai_api_key=settings.openai_api_key,
    )
    notifier = TelegramNotifier(settings.telegram_token, settings.telegram_chat_id)

    processed_ids = load_processed_ids(settings.processed_store_path)
    emails = gmail.fetch_unread_emails(label="medium")

    for email in emails:
        if email.id in processed_ids:
            continue

        agent = router.route_email(email)
        result = agent.process(email)
        digest = summarizer.summarize(result)
        notifier.send_message(digest)

        gmail.mark_as_processed(email.id)
        processed_ids.add(email.id)

    save_processed_ids(settings.processed_store_path, processed_ids)


if __name__ == "__main__":
    main()
