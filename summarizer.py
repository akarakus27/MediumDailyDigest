"""OpenAI-powered summarizer for intelligence brief format."""

import os
from openai import OpenAI


MODEL = "gpt-4o-mini"


def prefix_for_title(title: str) -> str:
    """Return emoji prefix based on title keywords."""
    t = title.upper()
    if "BIGQUERY" in t:
        return "⭐ "
    if "INTERVIEW" in t:
        return "🎤 "
    if "AI" in t or "AGENT" in t:
        return "🤖 "
    return ""


SYSTEM_PROMPT = """You are a senior data engineer. Generate a dense, technical intelligence brief for the given article.

Output EXACTLY in this format (no extra text before or after):

Title: [Use the article title as-is]
Read Time: [X min read or "N/A" if unknown]

Topic:
[Exactly 1 sentence - technical topic summary]

Critical Technical Points:
• [Bullet 1 - specific technical fact]
• [Bullet 2]
• [Bullet 3]
• [Bullet 4]
• [Bullet 5]

Practical Takeaway:
[One actionable insight - what can the reader do with this knowledge]

Who Should Read This:
[Target audience - e.g. "Data engineers building ETL pipelines"]

Rules:
- No fluff or storytelling
- Dense technical summary only
- Maximum 5 bullets
- Keep each bullet under 80 chars when possible
- Be concise - this goes to Telegram"""


def summarize_article(
    content: str,
    title: str,
    url: str,
    read_time: str | None = None,
) -> str | None:
    """
    Generate intelligence brief for article.
    Returns formatted string or None on failure.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    client = OpenAI(api_key=api_key)

    read_time_str = read_time or "N/A"
    user_content = f"""Article URL: {url}
Article Title: {title}
Read Time: {read_time_str}

Article content (excerpt):
{content[:6000]}

Generate the intelligence brief in the exact format specified."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        prefix = prefix_for_title(title)
        if prefix:
            # Add prefix to title line
            lines = raw.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("Title:"):
                    lines[i] = f"Title: {prefix}{line[6:].strip()}"
                    break
            raw = "\n".join(lines)
        return raw
    except Exception as e:
        print(f"[Summarizer] Error: {e}")
        return None
