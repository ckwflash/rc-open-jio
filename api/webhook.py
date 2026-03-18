from __future__ import annotations

import logging

from fastapi import FastAPI, Header, HTTPException, Request

from app.bot import process_update
from app.config import settings

app = FastAPI()
logger = logging.getLogger(__name__)


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    if not settings.dev_mode:
        if not settings.webhook_secret:
            raise HTTPException(status_code=500, detail="Webhook secret is not configured")

        if x_telegram_bot_api_secret_token != settings.webhook_secret:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")

    update = await request.json()
    try:
        await process_update(update)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to process Telegram update")
    return {"ok": True}

@app.post("/api/webhook")
async def webhook(request: Request):
    update = await request.json()
    await process_update(update)
    return {"ok": True}
