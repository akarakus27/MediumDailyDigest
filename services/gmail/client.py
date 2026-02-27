from __future__ import annotations

import json
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.discovery_resource import Resource

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailClient:
    """Thin Gmail API wrapper with OAuth lifecycle management."""

    def __init__(self, credentials_json: str, token_json: str | None = None) -> None:
        self._credentials_json = credentials_json
        self._token_json = token_json

    def _build_credentials(self) -> tuple[Credentials, dict[str, Any]]:
        credentials_dict: dict[str, Any] = json.loads(self._credentials_json)
        creds: Credentials | None = None

        if self._token_json:
            token_dict: dict[str, Any] = json.loads(self._token_json)
            installed = credentials_dict.get("installed", {})
            creds = Credentials(
                token=token_dict.get("token"),
                refresh_token=token_dict.get("refresh_token"),
                token_uri=token_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
                client_id=token_dict.get("client_id") or installed.get("client_id"),
                client_secret=token_dict.get("client_secret") or installed.get("client_secret"),
                scopes=SCOPES,
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(credentials_dict, SCOPES)
                creds = flow.run_local_server(port=0)

        return creds, credentials_dict

    def get_service(self) -> Resource:
        creds, _ = self._build_credentials()
        return build("gmail", "v1", credentials=creds)
