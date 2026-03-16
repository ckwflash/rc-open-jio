from __future__ import annotations

from typing import Any

import httpx

from app.config import settings

BASE_URL = f"https://api.telegram.org/bot{settings.bot_token}"


async def send_message(chat_id: int, text: str, reply_markup: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"{BASE_URL}/sendMessage", json=payload)


async def answer_callback_query(callback_query_id: str, text: str | None = None) -> None:
    payload: dict[str, Any] = {
        "callback_query_id": callback_query_id,
    }
    if text:
        payload["text"] = text

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"{BASE_URL}/answerCallbackQuery", json=payload)
