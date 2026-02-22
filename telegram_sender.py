"""Telegram bot message sender."""

import os
import re
import requests


TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LENGTH = 4096
SEPARATOR = "━━━━━━━━━━━━━━━━━━"


def escape_markdown(text: str) -> str:
    """Escape special Markdown characters for Telegram."""
    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!])", r"\\\1", text)


def format_brief_for_telegram(
    raw_summary: str,
    article_num: int,
    date_str: str,
) -> str:
    """
    Convert raw summary to Telegram format with header.
    """
    # Map structured fields to our format
    title = "Untitled"
    read_time = "N/A"
    topic = ""
    bullets = []
    takeaway = ""
    audience = ""

    lines = raw_summary.split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("Title:"):
            title = line[6:].strip()
        elif line.startswith("Read Time:"):
            read_time = line[10:].strip()
        elif line.startswith("Topic:"):
            current_section = "topic"
        elif line.startswith("Critical Technical Points:"):
            current_section = "bullets"
        elif line.startswith("Practical Takeaway:"):
            current_section = "takeaway"
        elif line.startswith("Who Should Read This:"):
            current_section = "audience"
        elif current_section == "topic":
            topic = line
            current_section = None
        elif current_section == "bullets" and line.startswith("•"):
            bullets.append(line)
        elif current_section == "takeaway":
            takeaway = line
            current_section = None
        elif current_section == "audience":
            audience = line
            current_section = None

    num_emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"][article_num - 1]

    parts = [
        f"{num_emoji} {title}",
        f"⏱ {read_time}",
        "",
        "🧠 Topic:",
        topic or "N/A",
        "",
        "🔑 Critical Technical Points:",
        *bullets if bullets else ["• N/A"],
        "",
        "⚙ Practical Takeaway:",
        takeaway or "N/A",
        "",
        "👤 Who Should Read This:",
        audience or "N/A",
    ]

    return "\n".join(parts)


def send_telegram_message(text: str) -> bool:
    """Send a single message to Telegram. Returns True on success."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")

    url = TELEGRAM_API.format(token=token)
    payload = {"chat_id": chat_id, "text": text}

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[Telegram] Send failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"[Telegram] Response: {e.response.text}")
        return False


def split_message(text: str, max_len: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Split long message into chunks at line boundaries."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    current = []
    current_len = 0

    for line in text.split("\n"):
        line_len = len(line) + 1
        if current_len + line_len > max_len and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len

    if current:
        chunks.append("\n".join(current))
    return chunks


def send_intelligence_brief(briefs: list[str], date_str: str) -> bool:
    """
    Send full intelligence brief to Telegram.
    Header + each article, split if needed.
    """
    header = f"☕ Medium Intelligence Brief\n{date_str}\n\n{SEPARATOR}\n\n"

    full_message = header
    for i, brief in enumerate(briefs):
        full_message += brief
        if i < len(briefs) - 1:
            full_message += f"\n\n{SEPARATOR}\n\n"

    for chunk in split_message(full_message):
        if not send_telegram_message(chunk):
            return False
    return True
