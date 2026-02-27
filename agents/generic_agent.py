from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from services.gmail.fetcher import EmailMessage


@dataclass(frozen=True)
class ArticleCandidate:
    title: str
    link: str
    preview: str


@dataclass(frozen=True)
class AgentResult:
    source: str
    email_id: str
    subject: str
    articles: list[ArticleCandidate]


class BaseAgent(ABC):
    @abstractmethod
    def process(self, email: EmailMessage) -> AgentResult:
        raise NotImplementedError


class GenericAgent(BaseAgent):
    """Fallback handler for unknown messages."""

    def process(self, email: EmailMessage) -> AgentResult:
        preview = re.sub(r"\s+", " ", email.body_text).strip()[:240]
        article = ArticleCandidate(
            title=email.subject or "Untitled Email",
            link=email.links[0] if email.links else "",
            preview=preview or email.snippet,
        )
        return AgentResult(
            source="generic",
            email_id=email.id,
            subject=email.subject,
            articles=[article],
        )
