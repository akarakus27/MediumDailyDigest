from __future__ import annotations

import json
from dataclasses import dataclass

import requests
from openai import OpenAI

from agents.generic_agent import AgentResult

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


@dataclass(frozen=True)
class SummarizationInput:
    source: str
    subject: str
    article_payload: str


class AISummarizer:
    """Single summarization service with Gemini-first + OpenAI fallback."""

    def __init__(self, gemini_api_key: str | None, openai_api_key: str | None) -> None:
        self.gemini_api_key = gemini_api_key
        self.openai_api_key = openai_api_key

    def summarize(self, result: AgentResult) -> str:
        payload = self._build_payload(result)
        if self.gemini_api_key:
            summary = self._summarize_with_gemini(payload)
            if summary:
                return summary
        if self.openai_api_key:
            summary = self._summarize_with_openai(payload)
            if summary:
                return summary
        raise RuntimeError("No AI provider available for summarization")

    def _build_payload(self, result: AgentResult) -> SummarizationInput:
        lines = []
        for idx, article in enumerate(result.articles, start=1):
            lines.append(
                f"[{idx}] title={article.title}\nlink={article.link}\nexcerpt={article.preview[:1000]}"
            )
        return SummarizationInput(
            source=result.source,
            subject=result.subject,
            article_payload="\n\n".join(lines),
        )

    def _prompt(self, payload: SummarizationInput) -> str:
        return (
            "Summarize this newsletter digest into concise intelligence. "
            "Use exactly this structure and markdown emojis:\n\n"
            "🧠 Medium Daily Intelligence\n\n"
            "🔥 Trending Topics\n"
            "📚 Key Articles\n"
            "⚡ Actionable Insights\n\n"
            f"Source: {payload.source}\n"
            f"Subject: {payload.subject}\n"
            f"Content:\n{payload.article_payload}\n"
        )

    def _summarize_with_gemini(self, payload: SummarizationInput) -> str | None:
        prompt = self._prompt(payload)
        body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.3, "maxOutputTokens": 450}}
        response = requests.post(
            f"{GEMINI_URL}?key={self.gemini_api_key}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(body),
            timeout=25,
        )
        if not response.ok:
            return None
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return None
        return parts[0].get("text")

    def _summarize_with_openai(self, payload: SummarizationInput) -> str | None:
        client = OpenAI(api_key=self.openai_api_key)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You generate concise intelligence-style newsletter digests."},
                {"role": "user", "content": self._prompt(payload)},
            ],
        )
        return completion.choices[0].message.content
