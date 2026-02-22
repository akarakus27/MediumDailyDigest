#!/usr/bin/env python3
"""
One-time Gmail OAuth helper.
Run locally to obtain GMAIL_TOKEN (refresh token) for use in GitHub Actions.

Usage:
  1. Create OAuth 2.0 credentials in Google Cloud Console
  2. Save as credentials.json in this directory
  3. Run: python auth_gmail.py
  4. Authorize in browser
  5. Copy token.json content to GMAIL_TOKEN secret
"""

import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from gmail_client import SCOPES

TOKEN_PATH = "token.json"
CREDS_PATH = "credentials.json"


def main() -> None:
    if not os.path.exists(CREDS_PATH):
        print(f"Place your OAuth credentials at {CREDS_PATH}")
        print("Get from: https://console.cloud.google.com/apis/credentials")
        return

    flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }

    with open(TOKEN_PATH, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"Saved to {TOKEN_PATH}")
    print("Add this file's content as GMAIL_TOKEN secret in GitHub.")


if __name__ == "__main__":
    main()
