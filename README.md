# Medium Intelligence Telegram Bot

Daily GitHub Action that fetches the Medium Daily Digest from Gmail, scrapes articles, generates technical intelligence briefs via OpenAI, and sends them to Telegram.

## Features

- Runs daily at 10:00 AM Turkey time (07:00 UTC)
- Fetches latest "Medium Daily Digest" from Gmail
- Extracts up to 5 Medium article links
- Scrapes full article content
- Generates dense technical summaries via GPT-4o-mini
- Sends structured briefs to Telegram
- Emoji prefixes: ⭐ BigQuery, 🎤 Interview, 🤖 AI/Agent

## Setup

### 1. GitHub Secrets

Add these repository secrets:

| Secret | Description |
|--------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `GMAIL_CREDENTIALS` | OAuth client JSON (from Google Cloud Console) |
| `GMAIL_TOKEN` | Token JSON with refresh_token (from auth flow) |

### 2. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download as `credentials.json`
5. Run locally:

```bash
pip install -r requirements.txt
python auth_gmail.py
```

6. Authorize in browser
7. Copy `token.json` content → `GMAIL_TOKEN` secret
8. Copy `credentials.json` content → `GMAIL_CREDENTIALS` secret

### 3. Telegram

- Create bot via [@BotFather](https://t.me/BotFather)
- Get your chat ID (e.g. via [@userinfobot](https://t.me/userinfobot))

## Local Run

```bash
export OPENAI_API_KEY=...
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
export GMAIL_CREDENTIALS='{"installed":{...}}'
export GMAIL_TOKEN='{"refresh_token":"...",...}'
python main.py
```

## Schedule

- Cron: `0 7 * * *` (07:00 UTC = 10:00 Turkey)
- Manual trigger: Workflow dispatch
