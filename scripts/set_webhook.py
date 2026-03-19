from __future__ import annotations

import os

import httpx
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "")
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    webhook_url = os.getenv("WEBHOOK_URL", "")

    if not token or not secret or not webhook_url:
        raise SystemExit("Please set BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET and WEBHOOK_URL in environment")

    url = f"https://api.telegram.org/bot{token}/setWebhook"
    payload = {
        "url": webhook_url,
        "secret_token": secret,
        "allowed_updates": ["message", "callback_query", "inline_query", "chosen_inline_result"],
        "drop_pending_updates": True,
    }

    with httpx.Client(timeout=20) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        print(response.json())

        commands_url = f"https://api.telegram.org/bot{token}/setMyCommands"
        commands_payload = {
            "commands": [
                {"command": "start", "description": "Start bot"},
                {"command": "menu", "description": "Show menu"},
                {"command": "list", "description": "Browse events"},
                {"command": "create", "description": "Create event"},
                {"command": "edit", "description": "Edit created event"},
                {"command": "joined", "description": "View joined events"},
                {"command": "created", "description": "View created events"},
                {"command": "subscribe", "description": "Subscribe categories"},
            ]
        }
        commands_response = client.post(commands_url, json=commands_payload)
        commands_response.raise_for_status()
        print(commands_response.json())


if __name__ == "__main__":
    main()
