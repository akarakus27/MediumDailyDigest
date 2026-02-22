"""Medium article scraper - extracts full article content."""

import re
import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MAX_CONTENT_LENGTH = 8000
REQUEST_TIMEOUT = 15


def scrape_article(url: str) -> tuple[str | None, str | None, str | None]:
    """
    Scrape Medium article content.
    Returns (content, title, read_time) or (None, None, None) on failure.
    """
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[Scraper] HTTP error for {url}: {e}")
        return None, None, None

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"[Scraper] Parse error for {url}: {e}")
        return None, None, None

    # Title: article h1 or meta
    title = None
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    if not title:
        meta = soup.find("meta", property="og:title")
        if meta and meta.get("content"):
            title = meta["content"]
    if not title:
        title = "Untitled"

    # Read time: look for common patterns
    read_time = None
    for pattern in [
        r"(\d+)\s*min\s*read",
        r"(\d+)\s*minute",
        r"read\s*time[:\s]*(\d+)",
    ]:
        match = re.search(pattern, resp.text, re.IGNORECASE)
        if match:
            read_time = f"{match.group(1)} min read"
            break

    # Content: article body paragraphs
    content_parts = []

    # Medium uses <article> and <p> inside section/div
    article = soup.find("article")
    if article:
        for p in article.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                content_parts.append(text)

    if not content_parts:
        # Fallback: any main content area
        for selector in ["[data-post-id]", "main", ".post-content", ".article-body"]:
            container = soup.select_one(selector)
            if container:
                for p in container.find_all("p"):
                    text = p.get_text(strip=True)
                    if text:
                        content_parts.append(text)
                if content_parts:
                    break

    if not content_parts:
        # Last resort: all p tags
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 50:  # Filter short/UI text
                content_parts.append(text)

    full_text = " ".join(content_parts)
    full_text = re.sub(r"\s+", " ", full_text).strip()
    full_text = full_text[:MAX_CONTENT_LENGTH]

    if len(full_text) < 100:
        print(f"[Scraper] Insufficient content for {url} ({len(full_text)} chars)")
        return None, None, None

    return full_text, title, read_time
