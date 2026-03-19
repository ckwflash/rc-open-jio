from __future__ import annotations

from typing import Any

import httpx

from app.config import settings

BASE_URL = f"https://api.telegram.org/bot{settings.bot_token}"
_CLIENT: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = httpx.AsyncClient(timeout=10)
    return _CLIENT


async def send_message(chat_id: int, text: str, reply_markup: dict[str, Any] | None = None) -> dict[str, Any] | None:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    response = await _get_client().post(f"{BASE_URL}/sendMessage", json=payload)
    if response.status_code == 200:
        return response.json().get("result")
    return None


async def answer_callback_query(callback_query_id: str, text: str | None = None) -> None:
    payload: dict[str, Any] = {
        "callback_query_id": callback_query_id,
    }
    if text:
        payload["text"] = text

    await _get_client().post(f"{BASE_URL}/answerCallbackQuery", json=payload)


async def edit_message_text(chat_id: int, message_id: int, text: str, reply_markup: dict[str, Any] | None = None) -> None:
    """Edit an existing message instead of sending a new one"""
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    await _get_client().post(f"{BASE_URL}/editMessageText", json=payload)
