from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException

from app.config import settings
from app.notifications import run_dispatch

app = FastAPI()


@app.get("/")
async def run_cron(authorization: str | None = Header(default=None)) -> dict[str, int]:
    if settings.cron_secret:
        expected = f"Bearer {settings.cron_secret}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Invalid cron authorization")

    return await run_dispatch(limit=100)
