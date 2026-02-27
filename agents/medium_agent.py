from __future__ import annotations

import re
from urllib.parse import urlparse

from agents.generic_agent import AgentResult, ArticleCandidate, BaseAgent
from services.gmail.fetcher import EmailMessage


class MediumAgent(BaseAgent):
    """Specialized extraction for Medium Daily Digest emails."""

    def __init__(self, max_articles: int = 5, max_preview_chars: int = 1000) -> None:
        self.max_articles = max_articles
        self.max_preview_chars = max_preview_chars

    def process(self, email: EmailMessage) -> AgentResult:
        medium_links = [
            link for link in email.links if "medium.com" in link and not any(x in link for x in ["/m/signin", "/topics/"])
        ]
        deduped_links = list(dict.fromkeys(medium_links))[: self.max_articles]

        normalized_text = re.sub(r"\s+", " ", email.body_text).strip()
        preview_text = normalized_text[: self.max_preview_chars]

        articles: list[ArticleCandidate] = []
        for link in deduped_links:
            title = self._title_from_link(link)
            snippet = self._extract_context(preview_text, link)
            articles.append(ArticleCandidate(title=title, link=link, preview=snippet))

        if not articles:
            articles.append(
                ArticleCandidate(
                    title=email.subject or "Medium Daily Digest",
                    link="",
                    preview=preview_text or email.snippet,
                )
            )

        return AgentResult(
            source="medium",
            email_id=email.id,
            subject=email.subject,
            articles=articles,
        )

    @staticmethod
    def _title_from_link(link: str) -> str:
        path = urlparse(link).path.strip("/")
        slug = path.split("/")[-1] if path else "medium-article"
        return slug.replace("-", " ").title()[:120]

    @staticmethod
    def _extract_context(text: str, link: str) -> str:
        if not text:
            return ""
        idx = text.find(link)
        if idx == -1:
            return text[:220]
        start = max(idx - 160, 0)
        end = min(idx + len(link) + 160, len(text))
        return text[start:end]
