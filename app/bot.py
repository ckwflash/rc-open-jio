from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.config import settings
from app.constants import ALLOWED_RCS, CATEGORY_KEYS, category_label
from app import repository
from app.telegram_api import answer_callback_query, send_message


def display_name(user: dict[str, Any]) -> str:
    first = user.get("first_name") or ""
    last = user.get("last_name") or ""
    full = f"{first} {last}".strip()
    return full or user.get("username") or "Telegram User"


def handle_text_or_command(text: str) -> str:
    return text.strip().split("@")[0].lower()


def category_buttons() -> list[list[dict[str, str]]]:
    rows: list[list[dict[str, str]]] = []
    for key in CATEGORY_KEYS:
        rows.append([{ "text": category_label(key), "callback_data": f"cat:{key}:0" }])
    rows.append([{ "text": "View All", "callback_data": "cat:all:0" }])
    return rows


async def process_update(update: dict[str, Any]) -> None:
    if "callback_query" in update:
        await _handle_callback_query(update["callback_query"])
        return

    message = update.get("message")
    if not message:
        return

    from_user = message.get("from")
    chat = message.get("chat")
    text = message.get("text") or ""
    if not from_user or not chat:
        return

    user = repository.upsert_user(
        telegram_user_id=from_user["id"],
        telegram_handle=from_user.get("username"),
        display_name=display_name(from_user),
    )

    command = handle_text_or_command(text)

    if command in {"/start", "/menu", "/help"}:
        await send_message(
            chat["id"],
            (
                "Welcome to RC Open Jio.\n\n"
                "Commands:\n"
                "/list - Browse events\n"
                "/create - Create event (quick format)\n"
                "/edit - Edit your event time/location\n"
                "/profile - Set preferred name and RC\n"
                "/joined - View joined events\n"
                "/created - View created events\n"
                "/subscribe - Subscribe to categories"
            ),
        )
        return

    if command.startswith("/profile"):
        await _handle_profile(chat["id"], user["id"], text)
        return

    if command == "/list":
        await send_message(
            chat["id"],
            "Choose a category:",
            {"inline_keyboard": category_buttons()},
        )
        return

    if command.startswith("/subscribe"):
        await send_message(
            chat["id"],
            "Choose a category to subscribe:",
            {"inline_keyboard": _subscription_buttons()},
        )
        return

    if command.startswith("/joined"):
        rows = repository.list_joined_events(user["id"])
        if not rows:
            await send_message(chat["id"], "You have not joined any events yet.")
            return
        lines = ["Your joined events:"]
        for event in rows:
            lines.append(f"- {event['title']} ({repository.format_dt(event['start_at'])})")
        await send_message(chat["id"], "\n".join(lines))
        return

    if command.startswith("/created"):
        rows = repository.list_created_events(user["id"])
        if not rows:
            await send_message(chat["id"], "You have not created any events yet.")
            return
        lines = ["Your created events:"]
        for event in rows:
            lines.append(f"- {event['title']} ({repository.format_dt(event['start_at'])}) | ID: {event['id']}")
        lines.append("\nEdit format:")
        lines.append("/edit EventID | YYYY-MM-DD HH:MM | New Location")
        await send_message(chat["id"], "\n".join(lines))
        return

    if command.startswith("/edit"):
        await _handle_edit(chat["id"], user["id"], text)
        return

    if command.startswith("/create"):
        await _handle_create(chat["id"], user["id"], text)
        return

    await send_message(chat["id"], "Use /menu to get started.")


async def _handle_create(chat_id: int, user_id: str, text: str) -> None:
    payload = text[len("/create"):].strip()
    if not payload:
        await send_message(
            chat_id,
            (
                "Create format:\n"
                "/create Title | CategoryKey | TargetAudience | YYYY-MM-DD HH:MM | Location | Capacity | Description\n\n"
                "Example:\n"
                "/create Badminton @ USC | sports_fitness | all_rc | 2026-03-20 19:30 | USC Hall | 12 | Casual doubles play"
            ),
        )
        return

    parts = [p.strip() for p in payload.split("|")]
    if len(parts) != 7:
        await send_message(chat_id, "Invalid format. Please use /create with 7 fields.")
        return

    title, category, target_audience, dt_str, location_text, cap_str, description = parts
    if category not in CATEGORY_KEYS:
        await send_message(chat_id, f"Invalid category key: {category}")
        return

    try:
        local_tz = ZoneInfo(settings.default_timezone)
        local_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
        start_at = local_dt.astimezone(UTC)
    except ValueError:
        await send_message(chat_id, "Invalid datetime format. Use YYYY-MM-DD HH:MM")
        return

    try:
        capacity = int(cap_str) if cap_str else None
    except ValueError:
        await send_message(chat_id, "Capacity must be a number.")
        return

    if capacity == 0:
        capacity = None

    event = repository.create_event(
        creator_user_id=user_id,
        title=title,
        description=description,
        category=category,
        target_audience=target_audience,
        start_at=start_at,
        location_text=location_text,
        capacity=capacity,
    )

    await send_message(chat_id, f"Event created: {event['title']} ({event['id']})")


async def _handle_edit(chat_id: int, user_id: str, text: str) -> None:
    payload = text[len("/edit"):].strip()
    if not payload:
        await send_message(chat_id, "Format: /edit EventID | YYYY-MM-DD HH:MM | New Location")
        return

    parts = [p.strip() for p in payload.split("|")]
    if len(parts) != 3:
        await send_message(chat_id, "Invalid format. Use: /edit EventID | YYYY-MM-DD HH:MM | New Location")
        return

    event_id, dt_str, new_location = parts

    try:
        local_tz = ZoneInfo(settings.default_timezone)
        local_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
        start_at = local_dt.astimezone(UTC)
    except ValueError:
        await send_message(chat_id, "Invalid datetime format. Use YYYY-MM-DD HH:MM")
        return

    ok, msg = repository.edit_event_schedule_location(
        creator_user_id=user_id,
        event_id=event_id,
        start_at=start_at,
        location_text=new_location,
    )
    await send_message(chat_id, msg if ok else f"Unable to edit event: {msg}")


async def _handle_callback_query(query: dict[str, Any]) -> None:
    data = query.get("data") or ""
    from_user = query.get("from") or {}
    message = query.get("message") or {}
    chat = message.get("chat") or {}

    if not from_user or not chat:
        return

    user = repository.upsert_user(
        telegram_user_id=from_user["id"],
        telegram_handle=from_user.get("username"),
        display_name=display_name(from_user),
    )

    if data.startswith("cat:"):
        await answer_callback_query(query["id"])
        _, category, page_s = data.split(":", 2)
        page = int(page_s)
        category_filter = None if category == "all" else category
        rows = repository.list_events(category=category_filter, page=page)

        if not rows:
            await send_message(chat["id"], "No events found.")
            return

        lines = ["Available events:"]
        keyboard: list[list[dict[str, str]]] = []
        for event in rows:
            lines.append(
                f"- {event['title']} | {category_label(event['category'])} | {repository.format_dt(event['start_at'])}"
            )
            keyboard.append([{ "text": f"Open: {event['title'][:25]}", "callback_data": f"evt:{event['id']}" }])

        if len(rows) == repository.PAGE_SIZE:
            keyboard.append([{ "text": "Next", "callback_data": f"cat:{category}:{page + 1}" }])

        await send_message(chat["id"], "\n".join(lines), {"inline_keyboard": keyboard})
        return

    if data.startswith("evt:"):
        await answer_callback_query(query["id"])
        event_id = data.split(":", 1)[1]
        event = repository.get_event(event_id)
        if not event:
            await send_message(chat["id"], "Event not found.")
            return

        participants = repository.get_event_participants(event_id)
        is_creator = event["creator_user_id"] == user["id"]

        participant_lines = []
        for p in participants:
            if is_creator:
                handle = f"@{p['telegram_handle']}" if p.get("telegram_handle") else "(no handle)"
                participant_lines.append(f"- {p['display_name']} {handle}")
            else:
                participant_lines.append(f"- {p['display_name']}")

        creator_handle = f"@{event['creator_handle']}" if event.get("creator_handle") else "(no handle)"

        text = (
            f"{event['title']}\n"
            f"Category: {category_label(event['category'])}\n"
            f"Audience: {event['target_audience']}\n"
            f"Time: {repository.format_dt(event['start_at'])}\n"
            f"Location: {event['location_text']}\n"
            f"Creator: {event['creator_name']} {creator_handle}\n"
            f"Description: {event['description']}\n\n"
            f"Participants ({len(participants)}):\n"
            + ("\n".join(participant_lines) if participant_lines else "- No participants yet")
        )

        keyboard = [
            [{ "text": "Join Event", "callback_data": f"jn:{event['id']}" }],
            [{ "text": "Subscribe Category", "callback_data": f"subc:{event['category']}" }],
        ]
        await send_message(chat["id"], text, {"inline_keyboard": keyboard})
        return

    if data.startswith("jn:"):
        event_id = data.split(":", 1)[1]
        ok, msg = repository.join_event(event_id, user["id"])
        await answer_callback_query(query["id"], "Joined" if ok else "Failed")
        await send_message(chat["id"], msg)
        return

    if data.startswith("subc:"):
        category = data.split(":", 1)[1]
        repository.subscribe_category(user["id"], category)
        await answer_callback_query(query["id"], "Subscribed")
        await send_message(chat["id"], f"Subscribed to {category_label(category)}")
        return

    await answer_callback_query(query["id"])


def _subscription_buttons() -> list[list[dict[str, str]]]:
    rows: list[list[dict[str, str]]] = []
    for key in CATEGORY_KEYS:
        rows.append([{ "text": category_label(key), "callback_data": f"subc:{key}" }])
    return rows


async def _handle_profile(chat_id: int, user_id: str, text: str) -> None:
    payload = text[len("/profile"):].strip()
    if not payload:
        profile = repository.get_profile(user_id)
        if not profile:
            await send_message(chat_id, "Profile not found.")
            return
        await send_message(
            chat_id,
            (
                f"Current profile:\n"
                f"Name: {profile['effective_display_name']}\n"
                f"RC: {profile.get('rc_name') or '-'}\n\n"
                f"Set format:\n/profile Preferred Name | RC Name\n"
                f"Allowed RCs: {', '.join(ALLOWED_RCS)}\n"
                f"Example:\n/profile Kaiwen | Tembusu"
            ),
        )
        return

    parts = [p.strip() for p in payload.split("|", 1)]
    if len(parts) != 2:
        await send_message(chat_id, "Use: /profile Preferred Name | RC Name")
        return

    preferred_name, rc_name = parts
    preferred_name = preferred_name[:80]
    rc_name = rc_name[:80]
    try:
        repository.set_profile(user_id, preferred_name or None, rc_name or None)
    except ValueError as ex:
        await send_message(chat_id, str(ex))
        return
    await send_message(chat_id, f"Profile updated. Name: {preferred_name or '-'} | RC: {rc_name or '-'}")
