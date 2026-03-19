from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.config import settings
from app.constants import ALLOWED_RCS, ALLOWED_RCS_MAP, CATEGORY_KEYS, CATEGORY_NAME_TO_KEY, category_label
from app import repository
from app.telegram_api import answer_callback_query, answer_inline_query, send_message, edit_message_text


MAIN_MENU_TEXT = (
    "Welcome to RC Open Jio.\n"
    "Tap an option below to continue."
)

MAIN_MENU_KEYBOARD = {
    "keyboard": [
        [{"text": "Browse events"}, {"text": "Create event"}],
        [{"text": "My joined events"}, {"text": "My created events"}],
        [{"text": "Subscribe categories"}, {"text": "Profile"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}

LIST_FLOW_KEYBOARD = {
    "keyboard": [
        [{"text": "Browse events"}, {"text": "Subscribe categories"}],
        [{"text": "◀️ Home"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}

CREATED_FLOW_KEYBOARD = {
    "keyboard": [
        [{"text": "Edit my event"}, {"text": "Delete my event"}],
        [{"text": "Create event"}, {"text": "◀️ Home"}],
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
    "delete my event": "/delete",
    "subscribe categories": "/subscribe",
    "profile": "/profile",
    "show main menu": "/menu",
    "◀️ home": "/menu",
    "❌ cancel": "/cancel",
}

FLOW_ONBOARDING = "onboarding"
FLOW_CREATE = "create"
FLOW_EDIT = "edit"
FLOW_DELETE = "delete"
FLOW_PROFILE = "profile"
FLOW_SUBSCRIBE = "subscribe"


def _set_flow_state(user_id: str, flow_type: str, state: dict[str, Any]) -> None:
    repository.set_user_flow_state(user_id, flow_type, state)


def _get_flow_state(user_id: str, flow_type: str) -> dict[str, Any] | None:
    return repository.get_user_flow_state(user_id, flow_type)


def _clear_flow_state(user_id: str, flow_type: str) -> None:
    repository.clear_user_flow_state(user_id, flow_type)

FLOW_ACTIONS_KEYBOARD = {
    "keyboard": [
        [{"text": "❌ Cancel"}, {"text": "◀️ Home"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}

EDIT_FIELD_CHOICE_KEYBOARD = {
    "keyboard": [
        [{"text": "Title"}, {"text": "Description"}],
        [{"text": "Category"}, {"text": "Target Audience"}],
        [{"text": "Date & Time"}, {"text": "Location"}],
        [{"text": "Capacity"}],
        [{"text": "❌ Cancel"}, {"text": "◀️ Home"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}


def _build_category_picker_keyboard() -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    labels = [category_label(key) for key in CATEGORY_KEYS]
    for i in range(0, len(labels), 2):
        row: list[dict[str, str]] = [{"text": labels[i]}]
        if i + 1 < len(labels):
            row.append({"text": labels[i + 1]})
        rows.append(row)

    rows.append([{"text": "❌ Cancel"}, {"text": "◀️ Home"}])
    return {
        "keyboard": rows,
        "resize_keyboard": True,
        "is_persistent": True,
    }


CATEGORY_PICKER_KEYBOARD = _build_category_picker_keyboard()


def _build_browse_category_keyboard() -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    labels = [category_label(key) for key in CATEGORY_KEYS]
    for i in range(0, len(labels), 2):
        row: list[dict[str, str]] = [{"text": labels[i]}]
        if i + 1 < len(labels):
            row.append({"text": labels[i + 1]})
        rows.append(row)

    rows.append([{"text": "View All"}])
    rows.append([{"text": "❌ Cancel"}, {"text": "◀️ Home"}])
    return {
        "keyboard": rows,
        "resize_keyboard": True,
        "is_persistent": True,
    }


BROWSE_CATEGORY_KEYBOARD = _build_browse_category_keyboard()


def _build_subscribe_category_keyboard() -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    labels = [category_label(key) for key in CATEGORY_KEYS]
    for i in range(0, len(labels), 2):
        row: list[dict[str, str]] = [{"text": labels[i]}]
        if i + 1 < len(labels):
            row.append({"text": labels[i + 1]})
        rows.append(row)

    rows.append([{"text": "❌ Cancel"}, {"text": "◀️ Home"}])
    return {
        "keyboard": rows,
        "resize_keyboard": True,
        "is_persistent": True,
    }


SUBSCRIBE_CATEGORY_KEYBOARD = _build_subscribe_category_keyboard()

SUBSCRIBE_MENU_KEYBOARD = {
    "keyboard": [
        [{"text": "Subscribe category"}, {"text": "Remove subscription"}],
        [{"text": "Browse events"}, {"text": "◀️ Home"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}

PROFILE_MENU_KEYBOARD = {
    "keyboard": [
        [{"text": "Edit Name"}, {"text": "Edit RC"}],
        [{"text": "❌ Cancel"}, {"text": "◀️ Home"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}


def _build_rc_picker_keyboard() -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    for i in range(0, len(ALLOWED_RCS), 2):
        row: list[dict[str, str]] = [{"text": ALLOWED_RCS[i]}]
        if i + 1 < len(ALLOWED_RCS):
            row.append({"text": ALLOWED_RCS[i + 1]})
        rows.append(row)

    rows.append([{"text": "❌ Cancel"}, {"text": "◀️ Home"}])
    return {
        "keyboard": rows,
        "resize_keyboard": True,
        "is_persistent": True,
    }


RC_PICKER_KEYBOARD = _build_rc_picker_keyboard()


def _build_audience_picker_keyboard() -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = [[{"text": "All RCs"}]]
    for i in range(0, len(ALLOWED_RCS), 2):
        row: list[dict[str, str]] = [{"text": ALLOWED_RCS[i]}]
        if i + 1 < len(ALLOWED_RCS):
            row.append({"text": ALLOWED_RCS[i + 1]})
        rows.append(row)

    rows.append([{"text": "❌ Cancel"}, {"text": "◀️ Home"}])
    return {
        "keyboard": rows,
        "resize_keyboard": True,
        "is_persistent": True,
    }


AUDIENCE_PICKER_KEYBOARD = _build_audience_picker_keyboard()


def display_name(user: dict[str, Any]) -> str:
    first = user.get("first_name") or ""
    last = user.get("last_name") or ""
    full = f"{first} {last}".strip()
    return full or user.get("username") or "Telegram User"


def handle_text_or_command(text: str) -> str:
    normalized = text.strip().lower()

    if normalized.startswith("◀") or normalized.startswith("⬅"):
        return "/menu"
    if normalized.startswith("❌"):
        return "/cancel"

    if normalized in BUTTON_TO_COMMAND:
        return BUTTON_TO_COMMAND[normalized]
    if normalized.startswith("/"):
        return normalized.split(maxsplit=1)[0].split("@")[0]
    return normalized


def _category_from_text(text: str) -> str | None:
    value = text.strip().lower()
    if value == "view all":
        return "all"
    return CATEGORY_NAME_TO_KEY.get(value)


def _audience_label(value: str | None) -> str:
    if not value:
        return "-"
    lowered = value.strip().lower()
    if lowered in {"all", "all_rc", "all rcs", "everyone"}:
        return "ALL RCS"
    canonical = ALLOWED_RCS_MAP.get(lowered, value.strip())
    return canonical.upper()


def _profile_summary(profile: dict[str, Any] | None) -> str:
    name = profile["effective_display_name"] if profile else "-"
    rc_name = _audience_label(profile.get("rc_name") if profile else None)
    return f"NAME: {name}\nRC: {rc_name}"


def _event_text(
    event: dict[str, Any],
    participants: list[dict[str, Any]],
    is_creator: bool,
    include_participant_handles: bool = False,
) -> str:
    participant_lines: list[str] = []
    for p in participants:
        if is_creator and include_participant_handles:
            handle = f"@{p['telegram_handle']}" if p.get("telegram_handle") else "(no handle)"
            participant_lines.append(f"- {p['display_name']} {handle}")
        else:
            participant_lines.append(f"- {p['display_name']}")

    creator_handle = f"@{event['creator_handle']}" if event.get("creator_handle") else "(no handle)"
    capacity = event.get("capacity")
    participant_count = len(participants)
    if capacity is None:
        limit_line = f"PARTICIPANT LIMIT: NO LIMIT ({participant_count} joined)"
    else:
        remaining = max(capacity - participant_count, 0)
        limit_line = f"PARTICIPANT LIMIT: {participant_count}/{capacity} ({remaining} spots left)"

    return (
        f"📌 {event['title']}\n"
        f"CATEGORY: {category_label(event['category']).upper()}\n"
        f"AUDIENCE: {_audience_label(event['target_audience'])}\n"
        f"TIME: {repository.format_dt(event['start_at'])}\n"
        f"LOCATION: {event['location_text']}\n"
        f"CREATOR: {event['creator_name']} {creator_handle}\n"
        f"{limit_line}\n"
        f"DESCRIPTION: {event['description']}\n\n"
        f"PARTICIPANTS ({participant_count}):\n"
        + ("\n".join(participant_lines) if participant_lines else "- No participants yet")
    )


def _share_query_for_event(event: dict[str, Any]) -> str:
    event_id = str(event.get("id") or "").strip()
    return f"evt:{event_id}" if event_id else ""


def _build_event_inline_keyboard(event: dict[str, Any], has_joined: bool, is_creator: bool) -> list[list[dict[str, str]]]:
    rows: list[list[dict[str, str]]] = []
    event_id = str(event["id"])

    if not is_creator:
        if has_joined:
            rows.append([{"text": "Leave Event", "callback_data": f"leave:{event_id}"}])
        else:
            rows.append([{"text": "Join Event", "callback_data": f"jn:{event_id}"}])

    rows.append([{"text": "Share Event", "switch_inline_query": _share_query_for_event(event)}])
    return rows


async def _edit_callback_message(
    query: dict[str, Any],
    text: str,
    reply_markup: dict[str, Any] | None = None,
) -> None:
    message = query.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    message_id = message.get("message_id")
    inline_message_id = query.get("inline_message_id")
    await edit_message_text(
        text=text,
        chat_id=chat_id,
        message_id=message_id,
        inline_message_id=inline_message_id,
        reply_markup=reply_markup,
    )


def _build_inline_event_result(
    event: dict[str, Any],
    participants: list[dict[str, Any]],
) -> dict[str, Any]:
    event_payload = dict(event)
    event_payload.setdefault("creator_name", "Event Creator")
    event_payload.setdefault("creator_handle", None)
    message_text = _event_text(
        event_payload,
        participants,
        is_creator=False,
        include_participant_handles=False,
    )
    return {
        "type": "article",
        "id": f"evt:{event['id']}",
        "title": event["title"],
        "description": f"{category_label(event['category'])} • {repository.format_dt(event['start_at'])}",
        "input_message_content": {
            "message_text": message_text,
            "disable_web_page_preview": True,
        },
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "Join Event", "callback_data": f"jn:{event['id']}"},
                {"text": "Leave Event", "callback_data": f"leave:{event['id']}"},
            ], [
                {"text": "Share Event", "switch_inline_query": _share_query_for_event(event)},
            ]]
        },
    }


def _build_shared_event_reply_markup(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "Join Event", "callback_data": f"jn:{event['id']}"},
                {"text": "Leave Event", "callback_data": f"leave:{event['id']}"},
            ],
            [
                {"text": "Share Event", "switch_inline_query": _share_query_for_event(event)},
            ],
        ]
    }


async def _refresh_shared_event_messages(event_id: str) -> None:
    event = repository.get_event(event_id)
    if not event:
        return
    participants = repository.get_event_participants(event_id)
    text = _event_text(event, participants, is_creator=False, include_participant_handles=False)
    reply_markup = _build_shared_event_reply_markup(event)
    inline_ids = repository.list_shared_event_message_ids(event_id)
    for inline_message_id in inline_ids:
        await edit_message_text(
            text=text,
            inline_message_id=inline_message_id,
            reply_markup=reply_markup,
        )


async def _handle_chosen_inline_result(chosen: dict[str, Any]) -> None:
    result_id = str(chosen.get("result_id") or "")
    inline_message_id = str(chosen.get("inline_message_id") or "")
    if not result_id.startswith("evt:") or not inline_message_id:
        return
    event_id = result_id[4:]
    if not event_id:
        return
    repository.register_shared_event_message(event_id, inline_message_id)


async def _send_event_detail(chat_id: int, event_id: str, viewer_user_id: str) -> None:
    event = repository.get_event(event_id)
    if not event:
        await send_message(chat_id, "Event not found.")
        return

    participants = repository.get_event_participants(event_id)
    is_creator = event["creator_user_id"] == viewer_user_id
    text = _event_text(event, participants, is_creator, include_participant_handles=is_creator)

    participant_ids = {p["user_id"] for p in participants}
    has_joined = viewer_user_id in participant_ids
    keyboard = _build_event_inline_keyboard(event, has_joined=has_joined, is_creator=is_creator)
    if keyboard:
        await send_message(chat_id, text, {"inline_keyboard": keyboard})
    else:
        await send_message(chat_id, text)


async def _handle_inline_query(inline_query: dict[str, Any]) -> None:
    query_id = inline_query.get("id")
    from_user = inline_query.get("from") or {}
    query_text = (inline_query.get("query") or "").strip()
    if not query_id or not from_user:
        return

    user = repository.upsert_user(
        telegram_user_id=from_user["id"],
        telegram_handle=from_user.get("username"),
        display_name=display_name(from_user),
    )

    lowered = query_text.lower()
    results: list[dict[str, Any]] = []
    if lowered.startswith("evt:"):
        event_id = query_text[4:].strip()
        event = repository.get_event(event_id)
        if event:
            participants = repository.get_event_participants(event_id)
            results.append(_build_inline_event_result(event, participants))
        await answer_inline_query(query_id, results, cache_time=0)
        return

    profile = repository.get_profile(user["id"])
    viewer_rc = profile.get("rc_name") if profile else None

    visible_events = repository.list_events(category=None, page=0, viewer_rc=viewer_rc)
    created_events = repository.list_created_events(user["id"])

    combined: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for event in created_events + visible_events:
        event_id = str(event["id"])
        if event_id in seen_ids:
            continue
        seen_ids.add(event_id)
        combined.append(event)

    for event in combined:
        event_id = str(event.get("id") or "")
        haystack = " ".join(
            [
                event_id,
                str(event.get("title") or ""),
                str(event.get("description") or ""),
                str(event.get("location_text") or ""),
                category_label(str(event.get("category") or "")),
            ]
        ).lower()
        if lowered and lowered not in haystack:
            continue

        event_for_render = event
        if "creator_name" not in event_for_render:
            full_event = repository.get_event(event_id)
            if full_event:
                event_for_render = full_event

        participants = repository.get_event_participants(str(event["id"]))
        results.append(_build_inline_event_result(event_for_render, participants))
        if len(results) >= 20:
            break

    await answer_inline_query(query_id, results, cache_time=0)


def category_buttons() -> list[list[dict[str, str]]]:
    rows: list[list[dict[str, str]]] = []
    for key in CATEGORY_KEYS:
        rows.append([{ "text": category_label(key), "callback_data": f"cat:{key}:0" }])
    rows.append([{ "text": "View All", "callback_data": "cat:all:0" }])
    return rows


async def process_update(update: dict[str, Any]) -> None:
    if "chosen_inline_result" in update:
        await _handle_chosen_inline_result(update["chosen_inline_result"])
        return

    if "inline_query" in update:
        await _handle_inline_query(update["inline_query"])
        return

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
    profile = repository.get_profile(user["id"])

    raw_text = text.strip()
    command = handle_text_or_command(raw_text)
    user_id = user["id"]

    if command in {"/start", "/menu", "/help"}:
        _clear_user_flow(user_id)
        if not profile or not profile.get("rc_name"):
            _set_flow_state(user_id, FLOW_ONBOARDING, {"step": "rc"})
            await send_message(
                chat["id"],
                "Welcome to RC Open Jio. First, pick your RC to continue:",
                RC_PICKER_KEYBOARD,
            )
            return
        await send_message(chat["id"], MAIN_MENU_TEXT, MAIN_MENU_KEYBOARD)
        return

    if command in {"/create", "/edit", "/delete", "/list", "/subscribe", "/joined", "/created"} and (
        not profile or not profile.get("rc_name")
    ):
        _set_flow_state(user_id, FLOW_ONBOARDING, {"step": "rc"})
        await send_message(chat["id"], "Please set your RC first.", RC_PICKER_KEYBOARD)
        return

    if command in {"/cancel", "cancel action", "cancel"}:
        _clear_user_flow(user_id)
        await send_message(chat["id"], "Action cancelled.", MAIN_MENU_KEYBOARD)
        return

    if command == "/create":
        await _start_create_flow(chat["id"], user_id)
        return

    if command == "/edit":
        await _start_edit_flow(chat["id"], user_id)
        return

    if command == "/delete":
        await _start_delete_flow(chat["id"], user_id)
        return

    if _get_flow_state(user_id, FLOW_ONBOARDING):
        await _continue_onboarding_flow(chat["id"], user_id, raw_text)
        return

    if _get_flow_state(user_id, FLOW_CREATE):
        await _continue_create_flow(chat["id"], user_id, raw_text)
        return

    if _get_flow_state(user_id, FLOW_EDIT):
        await _continue_edit_flow(chat["id"], user_id, raw_text)
        return

    if _get_flow_state(user_id, FLOW_DELETE):
        await _continue_delete_flow(chat["id"], user_id, raw_text)
        return

    if _get_flow_state(user_id, FLOW_PROFILE):
        await _continue_profile_flow(chat["id"], user_id, raw_text)
        return

    if _get_flow_state(user_id, FLOW_SUBSCRIBE):
        await _continue_subscribe_flow(chat["id"], user_id, raw_text)
        return

    selected_category = _category_from_text(raw_text)
    if selected_category:
        if not profile or not profile.get("rc_name"):
            _set_flow_state(user_id, FLOW_ONBOARDING, {"step": "rc"})
            await send_message(chat["id"], "Set your RC first to browse events.", RC_PICKER_KEYBOARD)
            return
        await _send_event_list(
            chat_id=chat["id"],
            category=selected_category,
            page=0,
            viewer_rc=profile.get("rc_name"),
        )
        return

    if command.startswith("/profile"):
        await _start_profile_flow(chat["id"], user["id"])
        return

    if command == "/list":
        if not profile or not profile.get("rc_name"):
            _set_flow_state(user_id, FLOW_ONBOARDING, {"step": "rc"})
            await send_message(chat["id"], "Set your RC first to browse events.", RC_PICKER_KEYBOARD)
            return
        await send_message(
            chat["id"],
            "Choose a category from the keyboard below:",
            BROWSE_CATEGORY_KEYBOARD,
        )
        return

    if command.startswith("/subscribe"):
        if not profile or not profile.get("rc_name"):
            _set_flow_state(user_id, FLOW_ONBOARDING, {"step": "rc"})
            await send_message(chat["id"], "Set your RC first to manage subscriptions.", RC_PICKER_KEYBOARD)
            return
        await _start_subscribe_flow(chat["id"], user_id)
        return

    if command.startswith("/joined"):
        rows = repository.list_joined_events(user["id"])
        if not rows:
            await send_message(chat["id"], "You have not joined any events yet.", MAIN_MENU_KEYBOARD)
            return
        lines = ["Your joined events:"]
        keyboard: list[list[dict[str, str]]] = []
        for event in rows:
            lines.append(f"- {event['title']} ({repository.format_dt(event['start_at'])})")
            keyboard.append([{ "text": f"Open: {event['title'][:25]}", "callback_data": f"evt:{event['id']}" }])
        await send_message(chat["id"], "\n".join(lines), {"inline_keyboard": keyboard})
        await send_message(chat["id"], "Use the options below to continue.", MAIN_MENU_KEYBOARD)
        return

    if command.startswith("/created"):
        rows = repository.list_created_events(user["id"])
        if not rows:
            await send_message(chat["id"], "You have not created any events yet.", CREATED_FLOW_KEYBOARD)
            return
        lines = ["Your created events:"]
        keyboard: list[list[dict[str, str]]] = []
        for idx, event in enumerate(rows, start=1):
            lines.append(f"{idx}. {event['title']} ({repository.format_dt(event['start_at'])})")
            keyboard.append([{ "text": f"Open: {event['title'][:25]}", "callback_data": f"evt:{event['id']}" }])
        lines.append("\nUse the bottom keyboard to edit, delete, create, or go home.")
        await send_message(chat["id"], "\n".join(lines), {"inline_keyboard": keyboard})
        await send_message(chat["id"], "Use the options below to continue.", CREATED_FLOW_KEYBOARD)
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

    if target_audience.lower() in {"all", "all rcs", "all_rc", "everyone"}:
        target_audience = "all_rc"
    else:
        canonical_rc = ALLOWED_RCS_MAP.get(target_audience.lower())
        if not canonical_rc:
            await send_message(chat_id, f"Invalid target audience. Use All RCs or one of: {', '.join(ALLOWED_RCS)}", CREATED_FLOW_KEYBOARD)
            return
        target_audience = canonical_rc

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
    await _notify_category_subscribers_for_event(event)
    await send_message(chat_id, f"✅ Event created: {event['title']}", CREATED_FLOW_KEYBOARD)
    await _send_event_detail(chat_id, str(event["id"]), user_id)


async def _handle_edit(chat_id: int, user_id: str, text: str) -> None:
    payload = text[len("/edit"):].strip()
    if not payload:
        await send_message(chat_id, "Use /edit and pick event number from the guided flow.", CREATED_FLOW_KEYBOARD)
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
    repository.clear_all_user_flow_states(user_id)


async def _continue_onboarding_flow(chat_id: int, user_id: str, text: str) -> None:
    value = text.strip()
    canonical = ALLOWED_RCS_MAP.get(value.lower())
    if not canonical:
        await send_message(chat_id, "Please pick one RC from the keyboard.", RC_PICKER_KEYBOARD)
        return
    repository.set_profile(user_id, None, canonical)
    _clear_flow_state(user_id, FLOW_ONBOARDING)
    profile = repository.get_profile(user_id)
    await send_message(
        chat_id,
        (
            "✅ Profile setup complete.\n"
            f"{_profile_summary(profile)}\n\n"
            "If you want to change your name later, open Profile."
        ),
        MAIN_MENU_KEYBOARD,
    )


async def _start_profile_flow(chat_id: int, user_id: str) -> None:
    profile = repository.get_profile(user_id)
    _set_flow_state(user_id, FLOW_PROFILE, {"step": "menu"})
    await send_message(
        chat_id,
        (
            f"Current profile:\n{_profile_summary(profile)}\n\n"
            "Choose what to edit."
        ),
        PROFILE_MENU_KEYBOARD,
    )


async def _continue_profile_flow(chat_id: int, user_id: str, text: str) -> None:
    state = _get_flow_state(user_id, FLOW_PROFILE)
    if not state:
        return

    value = text.strip()
    if not value:
        await send_message(chat_id, "Please enter a value.", FLOW_ACTIONS_KEYBOARD)
        return

    if state["step"] == "menu":
        choice = value.lower()
        if choice == "edit name":
            state["step"] = "name"
            _set_flow_state(user_id, FLOW_PROFILE, state)
            await send_message(chat_id, "Enter your new display name.", FLOW_ACTIONS_KEYBOARD)
            return
        if choice == "edit rc":
            state["step"] = "rc"
            _set_flow_state(user_id, FLOW_PROFILE, state)
            await send_message(chat_id, "Pick your RC.", RC_PICKER_KEYBOARD)
            return
        await send_message(chat_id, "Choose one option from the keyboard.", PROFILE_MENU_KEYBOARD)
        return

    profile = repository.get_profile(user_id)
    current_name = profile.get("custom_display_name") if profile else None
    current_rc = profile.get("rc_name") if profile else None

    if state["step"] == "name":
        updated_name = value[:80]
        repository.set_profile(user_id, updated_name, current_rc)
        _clear_flow_state(user_id, FLOW_PROFILE)
        updated = repository.get_profile(user_id)
        await send_message(chat_id, f"✅ Profile updated.\n{_profile_summary(updated)}", MAIN_MENU_KEYBOARD)
        return

    if state["step"] == "rc":
        canonical = ALLOWED_RCS_MAP.get(value.lower())
        if not canonical:
            await send_message(chat_id, "Please pick one RC from the keyboard.", RC_PICKER_KEYBOARD)
            return
        repository.set_profile(user_id, current_name, canonical)
        _clear_flow_state(user_id, FLOW_PROFILE)
        updated = repository.get_profile(user_id)
        await send_message(chat_id, f"✅ Profile updated.\n{_profile_summary(updated)}", MAIN_MENU_KEYBOARD)
        return

async def _start_subscribe_flow(chat_id: int, user_id: str) -> None:
    categories = repository.list_category_subscriptions(user_id)
    lines = ["Your subscribed categories:"]
    if categories:
        for key in categories:
            lines.append(f"- {category_label(key)}")
    else:
        lines.append("- (none)")

    lines.append("\nChoose an action below.")
    _set_flow_state(user_id, FLOW_SUBSCRIBE, {"step": "menu"})
    await send_message(chat_id, "\n".join(lines), SUBSCRIBE_MENU_KEYBOARD)


async def _continue_subscribe_flow(chat_id: int, user_id: str, text: str) -> None:
    value = text.strip()
    state = _get_flow_state(user_id, FLOW_SUBSCRIBE)
    if not state:
        return

    step = state.get("step")

    if step == "menu":
        lower = value.lower()
        if lower == "subscribe category":
            state["step"] = "subscribe_pick"
            _set_flow_state(user_id, FLOW_SUBSCRIBE, state)
            await send_message(chat_id, "Pick a category to subscribe:", SUBSCRIBE_CATEGORY_KEYBOARD)
            return
        if lower == "remove subscription":
            categories = repository.list_category_subscriptions(user_id)
            if not categories:
                await send_message(chat_id, "You do not have any category subscriptions yet.", SUBSCRIBE_MENU_KEYBOARD)
                return

            rows: list[list[dict[str, str]]] = []
            labels = [category_label(key) for key in categories]
            for i in range(0, len(labels), 2):
                row: list[dict[str, str]] = [{"text": labels[i]}]
                if i + 1 < len(labels):
                    row.append({"text": labels[i + 1]})
                rows.append(row)
            rows.append([{"text": "❌ Cancel"}, {"text": "◀️ Home"}])
            state["step"] = "remove_pick"
            state["removable_categories"] = categories
            _set_flow_state(user_id, FLOW_SUBSCRIBE, state)
            await send_message(
                chat_id,
                "Pick a category to remove:",
                {"keyboard": rows, "resize_keyboard": True, "is_persistent": True},
            )
            return

        await send_message(chat_id, "Choose one action from the keyboard.", SUBSCRIBE_MENU_KEYBOARD)
        return

    key = CATEGORY_NAME_TO_KEY.get(value.lower())
    if not key or key not in CATEGORY_KEYS:
        await send_message(chat_id, "Please pick a category from the keyboard.", SUBSCRIBE_CATEGORY_KEYBOARD)
        return

    if step == "subscribe_pick":
        repository.subscribe_category(user_id, key)
        await send_message(chat_id, f"Subscribed to {category_label(key)}")
        await _start_subscribe_flow(chat_id, user_id)
        return

    if step == "remove_pick":
        removable = set(state.get("removable_categories") or [])
        if key not in removable:
            await send_message(chat_id, "Please pick one of your subscribed categories.")
            return
        removed = repository.remove_category_subscription(user_id, key)
        if removed:
            await send_message(chat_id, f"Removed subscription: {category_label(key)}")
        else:
            await send_message(chat_id, "Subscription was already removed.")
        await _start_subscribe_flow(chat_id, user_id)
        return

    await send_message(chat_id, "Subscription action ended.", LIST_FLOW_KEYBOARD)
    _clear_flow_state(user_id, FLOW_SUBSCRIBE)


async def _start_create_flow(chat_id: int, user_id: str) -> None:
    _set_flow_state(user_id, FLOW_CREATE, {"step": "title", "data": {}})
    await send_message(chat_id, "Creating event (1/7): Enter event title.", FLOW_ACTIONS_KEYBOARD)


async def _continue_create_flow(chat_id: int, user_id: str, text: str) -> None:
    state = _get_flow_state(user_id, FLOW_CREATE)
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
        _set_flow_state(user_id, FLOW_CREATE, state)
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
        _set_flow_state(user_id, FLOW_CREATE, state)
        await send_message(
            chat_id,
            "Creating event (3/7): Pick target audience.",
            AUDIENCE_PICKER_KEYBOARD,
        )
        return

    if step == "target_audience":
        if value.lower() == "all rcs":
            data["target_audience"] = "all_rc"
        else:
            canonical = ALLOWED_RCS_MAP.get(value.lower())
            if not canonical:
                await send_message(chat_id, "Invalid audience. Choose from keyboard.", AUDIENCE_PICKER_KEYBOARD)
                return
            data["target_audience"] = canonical
        state["step"] = "start_at"
        _set_flow_state(user_id, FLOW_CREATE, state)
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
        _set_flow_state(user_id, FLOW_CREATE, state)
        await send_message(chat_id, "Creating event (5/7): Enter location.", FLOW_ACTIONS_KEYBOARD)
        return

    if step == "location":
        data["location_text"] = value
        state["step"] = "capacity"
        _set_flow_state(user_id, FLOW_CREATE, state)
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
        _set_flow_state(user_id, FLOW_CREATE, state)
        await send_message(chat_id, "Creating event (7/7): Enter description.", FLOW_ACTIONS_KEYBOARD)
        return

    if step == "description":
        data["description"] = value
        start_at_value = data["start_at"]
        if isinstance(start_at_value, str):
            start_at_value = datetime.fromisoformat(start_at_value)
        event = repository.create_event(
            creator_user_id=user_id,
            title=data["title"],
            description=data["description"],
            category=data["category"],
            target_audience=data["target_audience"],
            start_at=start_at_value,
            location_text=data["location_text"],
            capacity=data["capacity"],
        )
        await _notify_category_subscribers_for_event(event)
        _clear_flow_state(user_id, FLOW_CREATE)
        await send_message(chat_id, f"✅ Event created: {event['title']}", CREATED_FLOW_KEYBOARD)
        await _send_event_detail(chat_id, str(event["id"]), user_id)


async def _start_edit_flow(chat_id: int, user_id: str) -> None:
    rows = repository.list_created_events(user_id)
    if not rows:
        await send_message(chat_id, "You have not created any events yet.", CREATED_FLOW_KEYBOARD)
        return

    lines = ["Editing event. Step 1/3: Enter event number:"]
    index_map: dict[str, str] = {}
    for idx, row in enumerate(rows, start=1):
        index_map[str(idx)] = str(row["id"])
        lines.append(f"{idx}. {row['title']} ({repository.format_dt(row['start_at'])})")

    _set_flow_state(user_id, FLOW_EDIT, {"step": "event_index", "data": {}, "index_map": index_map})
    await send_message(chat_id, "\n".join(lines), FLOW_ACTIONS_KEYBOARD)


async def _continue_edit_flow(chat_id: int, user_id: str, text: str) -> None:
    state = _get_flow_state(user_id, FLOW_EDIT)
    if not state:
        return

    value = text.strip()
    if not value:
        await send_message(chat_id, "Please enter a value.", FLOW_ACTIONS_KEYBOARD)
        return

    data = state["data"]
    step = state["step"]

    if step == "event_index":
        event_id = state["index_map"].get(value)
        if not event_id:
            await send_message(chat_id, "Invalid event number. Choose one from the list above.", FLOW_ACTIONS_KEYBOARD)
            return
        data["event_id"] = event_id
        state["step"] = "field_choice"
        _set_flow_state(user_id, FLOW_EDIT, state)
        await send_message(
            chat_id,
            "Editing event (2/3): Choose what to edit.",
            EDIT_FIELD_CHOICE_KEYBOARD,
        )
        return

    if step == "field_choice":
        choice = value.lower()
        field_map = {
            "title": "title",
            "description": "description",
            "category": "category",
            "target audience": "target_audience",
            "date & time": "start_at",
            "location": "location_text",
            "capacity": "capacity",
        }
        selected = field_map.get(choice)
        if not selected:
            await send_message(chat_id, "Choose one option from the keyboard.", EDIT_FIELD_CHOICE_KEYBOARD)
            return
        data["field"] = selected
        state["step"] = "field_value"
        _set_flow_state(user_id, FLOW_EDIT, state)

        if selected == "category":
            await send_message(chat_id, "Step 3/3: Pick a new category.", CATEGORY_PICKER_KEYBOARD)
            return
        if selected == "target_audience":
            await send_message(chat_id, "Step 3/3: Pick new target audience.", AUDIENCE_PICKER_KEYBOARD)
            return
        if selected == "start_at":
            await send_message(
                chat_id,
                f"Step 3/3: Enter new date/time in {settings.default_timezone} as YYYY-MM-DD HH:MM",
                FLOW_ACTIONS_KEYBOARD,
            )
            return
        if selected == "capacity":
            await send_message(chat_id, "Step 3/3: Enter new capacity or type 'none'.", FLOW_ACTIONS_KEYBOARD)
            return

        await send_message(chat_id, "Step 3/3: Enter new value.", FLOW_ACTIONS_KEYBOARD)
        return

    if step == "field_value":
        field = data.get("field")
        kwargs: dict[str, Any] = {}

        if field == "title":
            kwargs["title"] = value
        elif field == "description":
            kwargs["description"] = value
        elif field == "category":
            key = CATEGORY_NAME_TO_KEY.get(value.lower(), value.lower())
            if key not in CATEGORY_KEYS:
                await send_message(chat_id, "Invalid category. Please tap one from keyboard.", CATEGORY_PICKER_KEYBOARD)
                return
            kwargs["category"] = key
        elif field == "target_audience":
            if value.lower() == "all rcs":
                kwargs["target_audience"] = "all_rc"
            else:
                canonical = ALLOWED_RCS_MAP.get(value.lower())
                if not canonical:
                    await send_message(chat_id, "Invalid audience. Choose from keyboard.", AUDIENCE_PICKER_KEYBOARD)
                    return
                kwargs["target_audience"] = canonical
        elif field == "start_at":
            try:
                local_tz = ZoneInfo(settings.default_timezone)
                local_dt = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
                kwargs["start_at"] = local_dt.astimezone(UTC)
            except ValueError:
                await send_message(chat_id, "Invalid datetime format. Use YYYY-MM-DD HH:MM", FLOW_ACTIONS_KEYBOARD)
                return
        elif field == "location_text":
            kwargs["location_text"] = value
        elif field == "capacity":
            if value.lower() in {"none", "no limit", "unlimited"}:
                kwargs["capacity"] = -1
            else:
                try:
                    cap = int(value)
                    if cap <= 0:
                        raise ValueError
                    kwargs["capacity"] = cap
                except ValueError:
                    await send_message(chat_id, "Capacity must be a positive number or 'none'.", FLOW_ACTIONS_KEYBOARD)
                    return
        else:
            await send_message(chat_id, "Invalid edit field. Start again with /edit.", CREATED_FLOW_KEYBOARD)
            _clear_flow_state(user_id, FLOW_EDIT)
            return

        ok, msg = repository.edit_event_fields(
            creator_user_id=user_id,
            event_id=data["event_id"],
            **kwargs,
        )
        _clear_flow_state(user_id, FLOW_EDIT)
        await send_message(chat_id, msg if ok else f"Unable to edit event: {msg}", CREATED_FLOW_KEYBOARD)


async def _start_delete_flow(chat_id: int, user_id: str) -> None:
    rows = repository.list_created_events(user_id)
    if not rows:
        await send_message(chat_id, "You have not created any events yet.", CREATED_FLOW_KEYBOARD)
        return

    lines = ["Deleting event. Step 1/2: Enter event number:"]
    index_map: dict[str, str] = {}
    for idx, row in enumerate(rows, start=1):
        index_map[str(idx)] = str(row["id"])
        lines.append(f"{idx}. {row['title']} ({repository.format_dt(row['start_at'])})")

    _set_flow_state(user_id, FLOW_DELETE, {"step": "event_index", "data": {}, "index_map": index_map})
    await send_message(chat_id, "\n".join(lines), FLOW_ACTIONS_KEYBOARD)


async def _continue_delete_flow(chat_id: int, user_id: str, text: str) -> None:
    state = _get_flow_state(user_id, FLOW_DELETE)
    if not state:
        return

    value = text.strip()
    if not value:
        await send_message(chat_id, "Please enter a value.", FLOW_ACTIONS_KEYBOARD)
        return

    data = state["data"]
    step = state["step"]

    if step == "event_index":
        event_id = state["index_map"].get(value)
        if not event_id:
            await send_message(chat_id, "Invalid event number. Choose one from the list above.", FLOW_ACTIONS_KEYBOARD)
            return
        
        event = repository.get_event(event_id)
        if not event:
            await send_message(chat_id, "Event not found.", CREATED_FLOW_KEYBOARD)
            _clear_flow_state(user_id, FLOW_DELETE)
            return
        
        data["event_id"] = event_id
        data["event_title"] = event["title"]
        state["step"] = "confirm"
        _set_flow_state(user_id, FLOW_DELETE, state)
        await send_message(
            chat_id,
            f"⚠️ Are you sure you want to delete '{event['title']}'?\n\nAll participants will lose access to this event and reminders will be cancelled.\n\nType 'yes' to confirm or 'no' to cancel.",
            FLOW_ACTIONS_KEYBOARD,
        )
        return

    if step == "confirm":
        if value.lower() not in {"yes", "y"}:
            _clear_flow_state(user_id, FLOW_DELETE)
            await send_message(chat_id, f"Deletion of '{data.get('event_title')}' cancelled.", CREATED_FLOW_KEYBOARD)
            return

        ok, msg = repository.delete_event(
            creator_user_id=user_id,
            event_id=data["event_id"],
        )
        _clear_flow_state(user_id, FLOW_DELETE)
        await send_message(chat_id, msg if ok else f"Unable to delete event: {msg}", CREATED_FLOW_KEYBOARD)


async def _handle_callback_query(query: dict[str, Any]) -> None:
    data = query.get("data") or ""
    from_user = query.get("from") or {}
    message = query.get("message") or {}
    chat = message.get("chat") or {}

    if not from_user:
        return

    user = repository.upsert_user(
        telegram_user_id=from_user["id"],
        telegram_handle=from_user.get("username"),
        display_name=display_name(from_user),
    )
    profile = repository.get_profile(user["id"])

    if data.startswith("cat:"):
        await answer_callback_query(query["id"])
        if not chat:
            return
        if not profile or not profile.get("rc_name"):
            _set_flow_state(user["id"], FLOW_ONBOARDING, {"step": "rc"})
            await send_message(chat["id"], "Set your RC first to browse events.", RC_PICKER_KEYBOARD)
            return
        _, category, page_s = data.split(":", 2)
        page = int(page_s)
        await _send_event_list(
            chat_id=chat["id"],
            category=category,
            page=page,
            viewer_rc=profile.get("rc_name"),
        )
        return

    if data.startswith("evt:"):
        await answer_callback_query(query["id"])
        if not chat:
            return
        event_id = data.split(":", 1)[1]
        event = repository.get_event(event_id)
        if not event:
            await send_message(chat["id"], "Event not found.")
            return

        participants = repository.get_event_participants(event_id)
        participant_ids = {p["user_id"] for p in participants}
        has_joined = user["id"] in participant_ids

        is_creator = event["creator_user_id"] == user["id"]

        text = _event_text(event, participants, is_creator, include_participant_handles=is_creator)
        keyboard = _build_event_inline_keyboard(event, has_joined=has_joined, is_creator=is_creator)

        await send_message(chat["id"], text, {"inline_keyboard": keyboard})
        return

    if data == "created:edit":
        await answer_callback_query(query["id"])
        if not chat:
            return
        await _start_edit_flow(chat["id"], user["id"])
        return

    if data == "created:delete":
        await answer_callback_query(query["id"])
        if not chat:
            return
        await _start_delete_flow(chat["id"], user["id"])
        return

    if data.startswith("jn:"):
        event_id = data.split(":", 1)[1]
        inline_message_id = str(query.get("inline_message_id") or "")
        if inline_message_id:
            repository.register_shared_event_message(event_id, inline_message_id)

        ok, msg = repository.join_event(event_id, user["id"])

        if ok:
            event = repository.get_event(event_id)
            if not event:
                await answer_callback_query(query["id"], "✅ Joined!")
                return
            participants = repository.get_event_participants(event_id)
            is_creator = event["creator_user_id"] == user["id"]

            participant_ids = {p["user_id"] for p in participants}
            has_joined = user["id"] in participant_ids
            is_inline_shared = bool(query.get("inline_message_id"))
            if is_inline_shared:
                updated_text = _event_text(event, participants, is_creator=False, include_participant_handles=False)
                keyboard = _build_shared_event_reply_markup(event)["inline_keyboard"]
            else:
                updated_text = _event_text(event, participants, is_creator, include_participant_handles=is_creator)
                keyboard = _build_event_inline_keyboard(event, has_joined=has_joined, is_creator=is_creator)

            await _edit_callback_message(
                query,
                updated_text,
                {"inline_keyboard": keyboard},
            )

            if is_inline_shared:
                await _refresh_shared_event_messages(event_id)

            await answer_callback_query(query["id"], "✅ Joined!")
        else:
            await answer_callback_query(query["id"], msg)
            if chat:
                await send_message(chat["id"], msg)
        return

    if data.startswith("leave:"):
        event_id = data.split(":", 1)[1]
        inline_message_id = str(query.get("inline_message_id") or "")
        if inline_message_id:
            repository.register_shared_event_message(event_id, inline_message_id)

        ok, msg = repository.leave_event(event_id, user["id"])

        if ok:
            event = repository.get_event(event_id)
            if not event:
                await answer_callback_query(query["id"], "✅ Left event!")
                return
            participants = repository.get_event_participants(event_id)
            is_creator = event["creator_user_id"] == user["id"]

            participant_ids = {p["user_id"] for p in participants}
            has_joined = user["id"] in participant_ids
            is_inline_shared = bool(query.get("inline_message_id"))
            if is_inline_shared:
                updated_text = _event_text(event, participants, is_creator=False, include_participant_handles=False)
                keyboard = _build_shared_event_reply_markup(event)["inline_keyboard"]
            else:
                updated_text = _event_text(event, participants, is_creator, include_participant_handles=is_creator)
                keyboard = _build_event_inline_keyboard(event, has_joined=has_joined, is_creator=is_creator)

            await _edit_callback_message(
                query,
                updated_text,
                {"inline_keyboard": keyboard},
            )

            if is_inline_shared:
                await _refresh_shared_event_messages(event_id)

            await answer_callback_query(query["id"], "✅ Left event!")
        else:
            await answer_callback_query(query["id"], msg)
            if chat:
                await send_message(chat["id"], msg)
        return
    
    await answer_callback_query(query["id"])


async def _send_event_list(chat_id: int, category: str, page: int, viewer_rc: str | None) -> None:
    category_filter = None if category == "all" else category
    rows = repository.list_events(category=category_filter, page=page, viewer_rc=viewer_rc)

    if not rows:
        await send_message(chat_id, "No events found.")
        return

    lines: list[str] = []
    keyboard: list[list[dict[str, str]]] = []

    if category == "all":
        lines = ["📂 VIEW: ALL CATEGORIES", "Tap an event to open:"]
        grouped: dict[str, list[dict[str, Any]]] = {}
        for event in rows:
            grouped.setdefault(event["category"], []).append(event)

        category_order = [key for key in CATEGORY_KEYS if key in grouped]
        category_order.extend([key for key in grouped.keys() if key not in category_order])

        for cat_key in category_order:
            lines.append("")
            lines.append(f"— {category_label(cat_key).upper()} —")
            for idx, event in enumerate(grouped[cat_key], start=1):
                limit = "No limit" if event.get("capacity") is None else f"{event.get('participant_count', 0)}/{event.get('capacity')}"
                lines.append(
                    f"{idx}. {event['title']} | {repository.format_dt(event['start_at'])} | LIMIT {limit}"
                )
                keyboard.append([{"text": f"Open: {event['title'][:25]}", "callback_data": f"evt:{event['id']}"}])
    else:
        lines = [f"📂 CATEGORY: {category_label(category).upper()}", "Tap an event to open:"]
        for idx, event in enumerate(rows, start=1):
            limit = "No limit" if event.get("capacity") is None else f"{event.get('participant_count', 0)}/{event.get('capacity')}"
            lines.append(
                f"{idx}. {event['title']} | {repository.format_dt(event['start_at'])} | LIMIT {limit}"
            )
            keyboard.append([{"text": f"Open: {event['title'][:25]}", "callback_data": f"evt:{event['id']}"}])

    if len(rows) == repository.PAGE_SIZE:
        keyboard.append([{ "text": "Next", "callback_data": f"cat:{category}:{page + 1}" }])

    await send_message(chat_id, "\n".join(lines), {"inline_keyboard": keyboard})
    await send_message(chat_id, "Use the options below to continue.", LIST_FLOW_KEYBOARD)


async def _notify_category_subscribers_for_event(event: dict[str, Any]) -> None:
    recipients = repository.list_category_subscription_recipients(
        category=event["category"],
        target_audience=event["target_audience"],
        creator_user_id=event["creator_user_id"],
    )

    if not recipients:
        return

    text = (
        "New event in your subscribed category:\n"
        f"{event['title']}\n"
        f"Category: {category_label(event['category'])}\n"
        f"Time: {repository.format_dt(event['start_at'])}\n"
        f"Location: {event['location_text']}"
    )
    keyboard = [[{"text": f"Open: {event['title'][:25]}", "callback_data": f"evt:{event['id']}"}]]

    for chat_id in recipients:
        try:
            await send_message(chat_id, text, {"inline_keyboard": keyboard})
        except Exception:  # noqa: BLE001
            continue


def _subscription_buttons() -> list[list[dict[str, str]]]:
    rows: list[list[dict[str, str]]] = []
    for key in CATEGORY_KEYS:
        rows.append([{ "text": category_label(key), "callback_data": f"subc:{key}" }])
    return rows
