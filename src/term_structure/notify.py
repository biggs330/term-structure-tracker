"""Post chart + animation + regime label to Discord #journalclub.

Requires a Discord webhook URL, created in your server under:
Server Settings -> Integrations -> Webhooks -> New Webhook -> Copy URL.

Put it in a local .env file (gitignored, never commit it):
    DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
"""

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


def post_to_discord(message: str, file_paths: list[str] | None = None) -> requests.Response:
    """POST a message (and optional file attachments) to the Discord webhook."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL not set -- add it to a local .env file")

    if not file_paths:
        response = requests.post(webhook_url, json={"content": message})
        response.raise_for_status()
        return response

    opened_files = [open(path, "rb") for path in file_paths]
    try:
        files = {
            f"file{i}": (Path(path).name, handle)
            for i, (path, handle) in enumerate(zip(file_paths, opened_files))
        }
        response = requests.post(
            webhook_url,
            data={"payload_json": json.dumps({"content": message})},
            files=files,
        )
        response.raise_for_status()
        return response
    finally:
        for handle in opened_files:
            handle.close()
