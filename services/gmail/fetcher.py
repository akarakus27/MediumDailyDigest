from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from services.gmail.client import GmailClient
from services.gmail.filters import html_to_text_and_links, plain_to_links


@dataclass(frozen=True)
class EmailMessage:
    id: str
    thread_id: str
    subject: str
    sender: str
    snippet: str
    body_text: str
    links: list[str]
    labels: list[str]


class GmailFetcher:
    """Reusable Gmail access layer for unread and label based retrieval."""

    def __init__(self, client: GmailClient) -> None:
        self._service = client.get_service()

    def fetch_unread_emails(self, label: str | None = None, max_results: int = 10) -> list[EmailMessage]:
        query = "is:unread"
        if label:
            query += f" {label}"
        return self._fetch_messages(query=query, max_results=max_results)

    def fetch_by_label(self, label: str, max_results: int = 10) -> list[EmailMessage]:
        return self._fetch_messages(query=f"label:{label}", max_results=max_results)

    def mark_as_processed(self, message_id: str) -> None:
        self._service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()

    def _fetch_messages(self, query: str, max_results: int) -> list[EmailMessage]:
        resp = (
            self._service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        messages = resp.get("messages", [])
        return [self._to_email_message(m["id"]) for m in messages]

    def _to_email_message(self, message_id: str) -> EmailMessage:
        msg = (
            self._service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        payload: dict[str, Any] = msg.get("payload", {})
        headers = {h.get("name", "").lower(): h.get("value", "") for h in payload.get("headers", [])}

        text_parts: list[str] = []
        links: list[str] = []
        self._collect_parts(payload, text_parts, links)
        body_text = "\n".join(part for part in text_parts if part).strip()

        if not links and body_text:
            links.extend(plain_to_links(body_text))

        return EmailMessage(
            id=msg.get("id", ""),
            thread_id=msg.get("threadId", ""),
            subject=headers.get("subject", ""),
            sender=headers.get("from", ""),
            snippet=msg.get("snippet", ""),
            body_text=body_text,
            links=list(dict.fromkeys(links)),
            labels=msg.get("labelIds", []),
        )

    def _collect_parts(self, part: dict[str, Any], text_parts: list[str], links: list[str]) -> None:
        mime_type = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data")

        if body_data:
            decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
            if mime_type == "text/html":
                parsed = html_to_text_and_links(decoded)
                text_parts.append(parsed.text)
                links.extend(parsed.links)
            elif mime_type == "text/plain":
                text_parts.append(decoded)

        for subpart in part.get("parts", []) or []:
            self._collect_parts(subpart, text_parts, links)
