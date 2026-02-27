from __future__ import annotations

import requests


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str) -> None:
        self._token = token
        self._chat_id = chat_id

    def send_message(self, text: str) -> None:
        response = requests.post(
            f"https://api.telegram.org/bot{self._token}/sendMessage",
            json={
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        response.raise_for_status()
