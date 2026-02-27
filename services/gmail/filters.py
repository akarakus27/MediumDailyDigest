from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape

from bs4 import BeautifulSoup

MEDIUM_SUBJECT_PATTERN = re.compile(r"medium\s+daily\s+digest", re.IGNORECASE)
NEWSLETTER_SUBJECT_PATTERN = re.compile(r"newsletter|digest|daily", re.IGNORECASE)
LINK_PATTERN = re.compile(r"https?://[^\s\"'<>]+")


@dataclass(frozen=True)
class EmailContent:
    text: str
    links: list[str]


def html_to_text_and_links(html: str) -> EmailContent:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href")
        if href and href.startswith("http"):
            links.append(href)
    return EmailContent(text=unescape(text), links=links)


def plain_to_links(text: str) -> list[str]:
    return LINK_PATTERN.findall(text)


def is_medium_digest_subject(subject: str) -> bool:
    return bool(MEDIUM_SUBJECT_PATTERN.search(subject or ""))


def is_newsletter_subject(subject: str) -> bool:
    return bool(NEWSLETTER_SUBJECT_PATTERN.search(subject or ""))
