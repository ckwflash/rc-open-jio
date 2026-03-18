from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.config import settings
from app.constants import CATEGORY_KEYS, CATEGORY_LABELS, CATEGORY_NAME_TO_KEY
from app import repository
from app.telegram_api import answer_callback_query, send_message, edit_message_text


MAIN_MENU_TEXT = (
    "Welcome to RC Open Jio.\n"
    "Tap an option below to continue."
)

MAIN_MENU_KEYBOARD = {
    "keyboard": [
        [{"text": "Browse events"}, {"text": "Create event"}],
        [{"text": "My joined events"}, {"text": "My created events"}],
        [{"text": "Edit my event"}, {"text": "Subscribe categories"}],
        [{"text": "Show main menu"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}

LIST_FLOW_KEYBOARD = {
    "keyboard": [
        [{"text": "Browse events"}, {"text": "Subscribe categories"}],
        [{"text": "Show main menu"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}

CREATED_FLOW_KEYBOARD = {
    "keyboard": [
        [{"text": "Create event"}, {"text": "Edit my event"}],
        [{"text": "My created events"}, {"text": "Show main menu"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}

BUTTON_TO_COMMAND = {
    "browse events": "/list",
    "create event": "/create",
    "my joined events": "/joined",
    "my created events": "/created",
    "edit my event": "/edit",
    "subscribe categories": "/subscribe",
    "show main menu": "/menu",
}

CREATE_FLOWS: dict[str, dict[str, Any]] = {}
EDIT_FLOWS: dict[str, dict[str, Any]] = {}

FLOW_ACTIONS_KEYBOARD = {
    "keyboard": [
        [{"text": "Cancel action"}, {"text": "Show main menu"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}


def _build_category_picker_keyboard() -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    labels = list(CATEGORY_LABELS.values())
    for i in range(0, len(labels), 2):
        row: list[dict[str, str]] = [{"text": labels[i]}]
        if i + 1 < len(labels):
            row.append({"text": labels[i + 1]})
        rows.append(row)

    rows.append([{"text": "Cancel action"}, {"text": "Show main menu"}])
    return {
        "keyboard": rows,
        "resize_keyboard": True,
        "is_persistent": True,
    }


CATEGORY_PICKER_KEYBOARD = _build_category_picker_keyboard()


def display_name(user: dict[str, Any]) -> str:
    first = user.get("first_name") or ""
    last = user.get("last_name") or ""
    full = f"{first} {last}".strip()
    return full or user.get("username") or "Telegram User"


def handle_text_or_command(text: str) -> str:
    normalized = text.strip().lower()
    if normalized in BUTTON_TO_COMMAND:
        return BUTTON_TO_COMMAND[normalized]
    if normalized.startswith("/"):
        return normalized.split(maxsplit=1)[0].split("@")[0]
    return normalized


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

    raw_text = text.strip()
    command = handle_text_or_command(raw_text)
    user_id = user["id"]

    if command in {"/start", "/menu", "/help"}:
        _clear_user_flow(user_id)
        await send_message(chat["id"], MAIN_MENU_TEXT, MAIN_MENU_KEYBOARD)
        return

    if command in {"cancel action", "cancel"}:
        _clear_user_flow(user_id)
        await send_message(chat["id"], "Action cancelled.", MAIN_MENU_KEYBOARD)
        return

    if command == "/create":
        await _start_create_flow(chat["id"], user_id)
        return

    if command == "/edit":
        await _start_edit_flow(chat["id"], user_id)
        return

    if user_id in CREATE_FLOWS:
        await _continue_create_flow(chat["id"], user_id, raw_text)
        return

    if user_id in EDIT_FLOWS:
        await _continue_edit_flow(chat["id"], user_id, raw_text)
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
        await send_message(chat["id"], "You can continue from the options below too.", LIST_FLOW_KEYBOARD)
        return

    if command.startswith("/subscribe"):
        await send_message(
            chat["id"],
            "Choose a category to subscribe:",
            {"inline_keyboard": _subscription_buttons()},
        )
        await send_message(chat["id"], "Subscription options are shown above.", LIST_FLOW_KEYBOARD)
        return

    if command.startswith("/joined"):
        rows = repository.list_joined_events(user["id"])
        if not rows:
            await send_message(chat["id"], "You have not joined any events yet.", MAIN_MENU_KEYBOARD)
            return
        lines = ["Your joined events:"]
        for event in rows:
            lines.append(f"- {event['title']} ({repository.format_dt(event['start_at'])})")
        await send_message(chat["id"], "\n".join(lines), MAIN_MENU_KEYBOARD)
        return

    if command.startswith("/created"):
        rows = repository.list_created_events(user["id"])
        if not rows:
            await send_message(chat["id"], "You have not created any events yet.", CREATED_FLOW_KEYBOARD)
            return
        lines = ["Your created events:"]
        for event in rows:
            lines.append(f"- {event['title']} ({repository.format_dt(event['start_at'])}) | ID: {event['id']}")
        lines.append("\nTap 'Edit my event' below to update one.")
        await send_message(chat["id"], "\n".join(lines), CREATED_FLOW_KEYBOARD)
        return

    if command.startswith("/edit") and command != "/edit":
        await _handle_edit(chat["id"], user["id"], text)
        return

    if command.startswith("/create") and command != "/create":
        await _handle_create(chat["id"], user["id"], text)
        return

    await send_message(chat["id"], "Use /menu to get started.", MAIN_MENU_KEYBOARD)


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
            CREATED_FLOW_KEYBOARD,
        )
        return

    parts = [p.strip() for p in payload.split("|")]
    if len(parts) != 7:
        await send_message(chat_id, "Invalid format. Please use /create with 7 fields.", CREATED_FLOW_KEYBOARD)
        return

    title, category, target_audience, dt_str, location_text, cap_str, description = parts
    if category not in CATEGORY_KEYS:
        await send_message(chat_id, f"Invalid category key: {category}", CREATED_FLOW_KEYBOARD)
        return

    try:
        local_tz = ZoneInfo(settings.default_timezone)
        local_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
        start_at = local_dt.astimezone(UTC)
    except ValueError:
        await send_message(chat_id, "Invalid datetime format. Use YYYY-MM-DD HH:MM", CREATED_FLOW_KEYBOARD)
        return

    try:
        capacity = int(cap_str) if cap_str else None
    except ValueError:
        await send_message(chat_id, "Capacity must be a number.", CREATED_FLOW_KEYBOARD)
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
    await send_message(chat_id, f"Event created: {event['title']} ({event['id']})", CREATED_FLOW_KEYBOARD)


async def _handle_edit(chat_id: int, user_id: str, text: str) -> None:
    payload = text[len("/edit"):].strip()
    if not payload:
        await send_message(chat_id, "Format: /edit EventID | YYYY-MM-DD HH:MM | New Location", CREATED_FLOW_KEYBOARD)
        return

    parts = [p.strip() for p in payload.split("|")]
    if len(parts) != 3:
        await send_message(chat_id, "Invalid format. Use: /edit EventID | YYYY-MM-DD HH:MM | New Location", CREATED_FLOW_KEYBOARD)
        return

    event_id, dt_str, new_location = parts

    try:
        local_tz = ZoneInfo(settings.default_timezone)
        local_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
        start_at = local_dt.astimezone(UTC)
    except ValueError:
        await send_message(chat_id, "Invalid datetime format. Use YYYY-MM-DD HH:MM", CREATED_FLOW_KEYBOARD)
        return

    ok, msg = repository.edit_event_schedule_location(
        creator_user_id=user_id,
        event_id=event_id,
        start_at=start_at,
        location_text=new_location,
    )
    await send_message(chat_id, msg if ok else f"Unable to edit event: {msg}", CREATED_FLOW_KEYBOARD)


def _clear_user_flow(user_id: str) -> None:
    CREATE_FLOWS.pop(user_id, None)
    EDIT_FLOWS.pop(user_id, None)


async def _start_create_flow(chat_id: int, user_id: str) -> None:
    CREATE_FLOWS[user_id] = {"step": "title", "data": {}}
    await send_message(chat_id, "Creating event (1/7): Enter event title.", FLOW_ACTIONS_KEYBOARD)


async def _continue_create_flow(chat_id: int, user_id: str, text: str) -> None:
    state = CREATE_FLOWS.get(user_id)
    if not state:
        return

    value = text.strip()
    if not value:
        await send_message(chat_id, "Please enter a value.", FLOW_ACTIONS_KEYBOARD)
        return

    data = state["data"]
    step = state["step"]

    if step == "title":
        data["title"] = value
        state["step"] = "category"
        await send_message(
            chat_id,
            "Creating event (2/7): Pick a category from the options below.",
            CATEGORY_PICKER_KEYBOARD,
        )
        return

    if step == "category":
        key = CATEGORY_NAME_TO_KEY.get(value.lower(), value.lower())
        if key not in CATEGORY_KEYS:
            await send_message(chat_id, "Invalid category. Please tap one from the keyboard.", CATEGORY_PICKER_KEYBOARD)
            return
        data["category"] = key
        state["step"] = "target_audience"
        await send_message(
            chat_id,
            "Creating event (3/7): Enter target audience (e.g. all_rc, rc4_only, everyone).",
            FLOW_ACTIONS_KEYBOARD,
        )
        return

    if step == "target_audience":
        data["target_audience"] = value
        state["step"] = "start_at"
        await send_message(
            chat_id,
            f"Creating event (4/7): Enter start date/time in {settings.default_timezone} as YYYY-MM-DD HH:MM",
            FLOW_ACTIONS_KEYBOARD,
        )
        return

    if step == "start_at":
        try:
            local_tz = ZoneInfo(settings.default_timezone)
            local_dt = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
            data["start_at"] = local_dt.astimezone(UTC)
        except ValueError:
            await send_message(chat_id, "Invalid datetime format. Use YYYY-MM-DD HH:MM", FLOW_ACTIONS_KEYBOARD)
            return
        state["step"] = "location"
        await send_message(chat_id, "Creating event (5/7): Enter location.", FLOW_ACTIONS_KEYBOARD)
        return

    if step == "location":
        data["location_text"] = value
        state["step"] = "capacity"
        await send_message(
            chat_id,
            "Creating event (6/7): Enter capacity number, or type 'none' for no limit.",
            FLOW_ACTIONS_KEYBOARD,
        )
        return

    if step == "capacity":
        lower = value.lower()
        if lower in {"none", "no limit", "skip", "unlimited"}:
            data["capacity"] = None
        else:
            try:
                capacity = int(value)
                if capacity <= 0:
                    raise ValueError
                data["capacity"] = capacity
            except ValueError:
                await send_message(chat_id, "Capacity must be a positive number, or 'none'.", FLOW_ACTIONS_KEYBOARD)
                return
        state["step"] = "description"
        await send_message(chat_id, "Creating event (7/7): Enter description.", FLOW_ACTIONS_KEYBOARD)
        return

    if step == "description":
        data["description"] = value
        event = repository.create_event(
            creator_user_id=user_id,
            title=data["title"],
            description=data["description"],
            category=data["category"],
            target_audience=data["target_audience"],
            start_at=data["start_at"],
            location_text=data["location_text"],
            capacity=data["capacity"],
        )
        CREATE_FLOWS.pop(user_id, None)
        await send_message(chat_id, f"Event created: {event['title']} ({event['id']})", CREATED_FLOW_KEYBOARD)


async def _start_edit_flow(chat_id: int, user_id: str) -> None:
    rows = repository.list_created_events(user_id)
    if not rows:
        await send_message(chat_id, "You have not created any events yet.", CREATED_FLOW_KEYBOARD)
        return

    valid_ids = {str(row["id"]) for row in rows}
    lines = ["Editing event. Step 1/3: Enter Event ID from your list:"]
    for row in rows:
        lines.append(f"- {row['title']} | ID: {str(row['id'])}")

    EDIT_FLOWS[user_id] = {"step": "event_id", "data": {}, "valid_ids": valid_ids}
    await send_message(chat_id, "\n".join(lines), FLOW_ACTIONS_KEYBOARD)


async def _continue_edit_flow(chat_id: int, user_id: str, text: str) -> None:
    state = EDIT_FLOWS.get(user_id)
    if not state:
        return

    value = text.strip()
    if not value:
        await send_message(chat_id, "Please enter a value.", FLOW_ACTIONS_KEYBOARD)
        return

    data = state["data"]
    step = state["step"]

    if step == "event_id":
        if value not in state["valid_ids"]:
            await send_message(chat_id, "Invalid Event ID. Paste one from the list above.", FLOW_ACTIONS_KEYBOARD)
            return
        data["event_id"] = value
        state["step"] = "start_at"
        await send_message(
            chat_id,
            f"Editing event (2/3): Enter new date/time in {settings.default_timezone} as YYYY-MM-DD HH:MM",
            FLOW_ACTIONS_KEYBOARD,
        )
        return

    if step == "start_at":
        try:
            local_tz = ZoneInfo(settings.default_timezone)
            local_dt = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
            data["start_at"] = local_dt.astimezone(UTC)
        except ValueError:
            await send_message(chat_id, "Invalid datetime format. Use YYYY-MM-DD HH:MM", FLOW_ACTIONS_KEYBOARD)
            return
        state["step"] = "location"
        await send_message(chat_id, "Editing event (3/3): Enter new location.", FLOW_ACTIONS_KEYBOARD)
        return

    if step == "location":
        data["location_text"] = value
        ok, msg = repository.edit_event_schedule_location(
            creator_user_id=user_id,
            event_id=data["event_id"],
            start_at=data["start_at"],
            location_text=data["location_text"],
        )
        EDIT_FLOWS.pop(user_id, None)
        await send_message(chat_id, msg if ok else f"Unable to edit event: {msg}", CREATED_FLOW_KEYBOARD)


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
        
        # Get the original message from the callback query
        original_message = query.get("message", {})
        message_id = original_message.get("message_id")
        chat_id = original_message.get("chat", {}).get("id")
    
        
        # Join the event
        ok, msg = repository.join_event(event_id, user["id"])
        
        if ok:
            # Get updated event details
            event = repository.get_event(event_id)
            participants = repository.get_event_participants(event_id)
            is_creator = event["creator_user_id"] == user["id"]
            
            # Rebuild the participant lines (same as in evt: handler)
            participant_lines = []
            for p in participants:
                if is_creator:
                    handle = f"@{p['telegram_handle']}" if p.get("telegram_handle") else "(no handle)"
                    participant_lines.append(f"- {p['display_name']} {handle}")
                else:
                    participant_lines.append(f"- {p['display_name']}")
            
            creator_handle = f"@{event['creator_handle']}" if event.get("creator_handle") else "(no handle)"
            
            # Build the updated text (THIS IS THE updated_text VARIABLE)
            updated_text = (
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
            
            # Rebuild the keyboard (same buttons as before)
            keyboard = [
                [{ "text": "Join Event", "callback_data": f"jn:{event['id']}" }],
                [{ "text": "Subscribe Category", "callback_data": f"subc:{event['category']}" }],
            ]
            
            # EDIT the original message
            await edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=updated_text,
                reply_markup={"inline_keyboard": keyboard}
            )
            
            # Show a brief popup that they joined
            await answer_callback_query(query["id"], "✅ Joined!")
        else:
            print(f"Join failed: {msg}")
            await answer_callback_query(query["id"], "❌ Failed to join")
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
