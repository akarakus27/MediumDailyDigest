#!/usr/bin/env python3
"""
Medium Intelligence Telegram Bot
Fetches Medium Daily Digest from Gmail, scrapes articles, summarizes, sends to Telegram.
"""

import os
from datetime import datetime

from gmail_client import fetch_latest_digest_links
from scraper import scrape_article
from summarizer import summarize_article
from telegram_sender import format_brief_for_telegram, send_intelligence_brief


def main() -> None:
    """Run the daily intelligence brief pipeline."""
    # Validate required env vars early
    required = ["OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "GMAIL_CREDENTIALS"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"[Main] Missing required env: {', '.join(missing)}")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"[Main] Starting Medium Intelligence Brief for {date_str}")

    # 1. Fetch digest links from Gmail
    links = fetch_latest_digest_links()
    if not links:
        print("[Main] No digest found. Exiting.")
        return

    print(f"[Main] Processing up to {len(links)} articles")

    briefs = []
    valid_count = 0

    for i, url in enumerate(links):
        if valid_count >= 5:
            break

        print(f"[Main] [{i + 1}/{len(links)}] {url}")

        # 2. Scrape article
        content, title, read_time = scrape_article(url)
        if content is None:
            print(f"[Main] Skipping (scrape failed): {url}")
            continue

        # 3. Summarize
        summary = summarize_article(content, title, url, read_time)
        if summary is None:
            print(f"[Main] Skipping (summary failed): {url}")
            continue

        # 4. Format for Telegram
        brief = format_brief_for_telegram(summary, valid_count + 1, date_str)
        briefs.append(brief)
        valid_count += 1

    if not briefs:
        print("[Main] No valid articles to send.")
        return

    # 5. Send to Telegram
    if send_intelligence_brief(briefs, date_str):
        print(f"[Main] Sent {len(briefs)} articles to Telegram.")
    else:
        print("[Main] Failed to send to Telegram.")


if __name__ == "__main__":
    main()
