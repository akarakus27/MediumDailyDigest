from __future__ import annotations

from agents.generic_agent import BaseAgent, GenericAgent
from agents.medium_agent import MediumAgent
from agents.newsletter_agent import NewsletterAgent
from services.gmail.fetcher import EmailMessage
from services.gmail.filters import is_medium_digest_subject, is_newsletter_subject


class EmailRouter:
    """Declarative, extensible router for assigning processing agents."""

    def __init__(
        self,
        medium_agent: BaseAgent,
        newsletter_agent: BaseAgent,
        generic_agent: BaseAgent,
    ) -> None:
        self._rules: list[tuple[callable, BaseAgent]] = [
            (lambda email: is_medium_digest_subject(email.subject), medium_agent),
            (lambda email: is_newsletter_subject(email.subject), newsletter_agent),
        ]
        self._default = generic_agent

    def add_rule(self, predicate: callable, agent: BaseAgent) -> None:
        self._rules.append((predicate, agent))

    def route_email(self, email: EmailMessage) -> BaseAgent:
        for predicate, agent in self._rules:
            if predicate(email):
                return agent
        return self._default


def default_router(max_articles: int = 5, max_preview_chars: int = 1000) -> EmailRouter:
    return EmailRouter(
        medium_agent=MediumAgent(max_articles=max_articles, max_preview_chars=max_preview_chars),
        newsletter_agent=NewsletterAgent(),
        generic_agent=GenericAgent(),
    )
