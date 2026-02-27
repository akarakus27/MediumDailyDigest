from __future__ import annotations

import re

from agents.generic_agent import AgentResult, ArticleCandidate, BaseAgent
from services.gmail.fetcher import EmailMessage


class NewsletterAgent(BaseAgent):
    """Generic newsletter parser that extracts link + local text context."""

    def process(self, email: EmailMessage) -> AgentResult:
        compressed = re.sub(r"\s+", " ", email.body_text).strip()
        articles: list[ArticleCandidate] = []

        for idx, link in enumerate(email.links[:5], start=1):
            start = max(compressed.find(link) - 180, 0)
            preview = compressed[start:start + 220]
            articles.append(
                ArticleCandidate(
                    title=f"Newsletter item {idx}",
                    link=link,
                    preview=preview,
                )
            )

        if not articles:
            articles.append(
                ArticleCandidate(
                    title=email.subject or "Newsletter",
                    link="",
                    preview=compressed[:220] or email.snippet,
                )
            )

        return AgentResult(
            source="newsletter",
            email_id=email.id,
            subject=email.subject,
            articles=articles,
        )
