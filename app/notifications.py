from __future__ import annotations

from typing import Any

from app import repository
from app.telegram_api import send_message


async def run_dispatch(limit: int = 50) -> dict[str, int]:
    claimed = repository.claim_due_notifications(limit=limit, locker="vercel-cron")
    sent = 0
    failed = 0

    for item in claimed:
        try:
            user = repository.get_user_by_id(item["recipient_user_id"])
            if not user:
                repository.mark_notification_failed(item["id"], "Recipient not found")
                failed += 1
                continue

            text = _build_text(item)
            if text is None:
                repository.mark_notification_sent(item["id"])
                sent += 1
                continue

            await send_message(user["telegram_user_id"], text)
            repository.mark_notification_sent(item["id"])
            sent += 1
        except Exception as ex:  # noqa: BLE001
            repository.mark_notification_failed(item["id"], str(ex))
            failed += 1

    return {"claimed": len(claimed), "sent": sent, "failed": failed}


def _build_text(item: dict[str, Any]) -> str | None:
    event_id = item.get("event_id")
    kind = item["kind"]

    if kind in {"reminder_24h", "reminder_1h", "event_update"}:
        if not event_id:
            return None
        event = repository.get_event_for_notification(event_id)
        if not event:
            return None

        when = repository.format_dt(event["start_at"])
        if kind == "reminder_24h":
            return f"Reminder: Your event is in 24 hours.\n{event['title']}\n{when}\n{event['location_text']}"
        if kind == "reminder_1h":
            return f"Reminder: Your event is in 1 hour.\n{event['title']}\n{when}\n{event['location_text']}"
        return f"Event update:\n{event['title']}\n{when}\n{event['location_text']}"

    if kind == "new_event_subscription":
        payload = item.get("payload") or {}
        title = payload.get("title", "New event")
        category = payload.get("category", "")
        return f"New event from your subscription:\n{title}\nCategory: {category}"

    return None
