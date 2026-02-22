"""Gmail client for fetching Medium Daily Digest emails."""

import base64
import json
import os
import re
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SUBJECT_FILTER = "Medium Daily Digest"
MEDIUM_LINK_PATTERN = re.compile(
    r"https?://(?:www\.)?medium\.com/@[\w-]+/[\w-]+(?:-\w+)*",
    re.IGNORECASE,
)
MEDIUM_LINK_ALT = re.compile(
    r"https?://(?:www\.)?medium\.com/[\w@.-]+/[\w-]+(?:-\w+)*",
    re.IGNORECASE,
)
# username.medium.com/slug format
MEDIUM_LINK_SUBDOMAIN = re.compile(
    r"https?://[\w-]+\.medium\.com/[\w-]+(?:-\w+)*",
    re.IGNORECASE,
)


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    credentials_json = os.environ.get("GMAIL_CREDENTIALS")
    token_json = os.environ.get("GMAIL_TOKEN")

    if not credentials_json:
        raise ValueError("GMAIL_CREDENTIALS environment variable is required")

    credentials_dict = json.loads(credentials_json)

    # Try to load token from GMAIL_TOKEN
    if token_json:
        token_dict = json.loads(token_json)
        creds = Credentials(
            token=token_dict.get("token"),
            refresh_token=token_dict.get("refresh_token"),
            token_uri=token_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_dict.get("client_id") or credentials_dict.get("installed", {}).get("client_id"),
            client_secret=token_dict.get("client_secret") or credentials_dict.get("installed", {}).get("client_secret"),
            scopes=SCOPES,
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # For headless/CI: must have valid token with refresh_token
            raise ValueError(
                "GMAIL_TOKEN with refresh_token is required for automated runs. "
                "Run auth flow locally once to obtain token."
            )

    return build("gmail", "v1", credentials=creds)


def get_email_body(payload):
    """Extract HTML/plain text body from Gmail message payload."""
    body = ""
    if "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            if "text/html" in mime_type or "text/plain" in mime_type:
                data = part.get("body", {}).get("data")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    if "text/html" in mime_type:
                        return body
                    if not body:
                        body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    else:
        data = payload.get("body", {}).get("data")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    return body


def extract_medium_links(html_content: str) -> list[str]:
    """Extract unique Medium article URLs from HTML content (order preserved)."""
    all_matches = []
    for pattern in (MEDIUM_LINK_PATTERN, MEDIUM_LINK_ALT, MEDIUM_LINK_SUBDOMAIN):
        all_matches.extend(pattern.findall(html_content))
    # Remove duplicates while preserving first occurrence order
    seen = set()
    unique = []
    for link in all_matches:
        clean = link.split("?")[0].split("#")[0].rstrip("/")
        if clean not in seen:
            seen.add(clean)
            unique.append(link)
    return unique


def fetch_latest_digest_links() -> list[str] | None:
    """
    Fetch the latest Medium Daily Digest email and extract article links.
    Returns list of URLs or None if no digest found.
    """
    print("[Gmail] Connecting to Gmail API...")
    service = get_gmail_service()

    # Search for emails from last 1 day
    after = (datetime.utcnow() - timedelta(days=1)).strftime("%Y/%m/%d")
    query = f'after:{after} subject:"{SUBJECT_FILTER}"'

    print(f"[Gmail] Searching for: {query}")
    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=1)
        .execute()
    )

    messages = results.get("messages", [])
    if not messages:
        print("[Gmail] No Medium Daily Digest found in last 24 hours.")
        return None

    msg_id = messages[0]["id"]
    print(f"[Gmail] Found digest email: {msg_id}")

    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    payload = msg.get("payload", {})
    body = get_email_body(payload)

    if not body:
        print("[Gmail] Could not extract email body.")
        return None

    links = extract_medium_links(body)
    print(f"[Gmail] Extracted {len(links)} Medium links")
    return links[:5]  # Max 5 articles
