from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.config import settings
from app.constants import ALLOWED_RCS, ALLOWED_RCS_MAP, CATEGORY_KEYS, CATEGORY_NAME_TO_KEY, category_label
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
        [{"text": "Edit my event"}, {"text": "Delete my event"}],
        [{"text": "Subscribe categories"}, {"text": "Profile"}],
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
    "delete my event": "/delete",
    "subscribe categories": "/subscribe",
    "profile": "/profile",
    "show main menu": "/menu",
}

CREATE_FLOWS: dict[str, dict[str, Any]] = {}
EDIT_FLOWS: dict[str, dict[str, Any]] = {}
DELETE_FLOWS: dict[str, dict[str, Any]] = {}
PROFILE_FLOWS: dict[str, dict[str, Any]] = {}
ONBOARDING_FLOWS: dict[str, dict[str, Any]] = {}
SUBSCRIBE_FLOWS: dict[str, dict[str, Any]] = {}

FLOW_ACTIONS_KEYBOARD = {
    "keyboard": [
        [{"text": "Cancel action"}, {"text": "Show main menu"}],
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
        [{"text": "Cancel action"}, {"text": "Show main menu"}],
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

    rows.append([{"text": "Cancel action"}, {"text": "Show main menu"}])
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
    rows.append([{"text": "Cancel action"}, {"text": "Show main menu"}])
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

    rows.append([{"text": "Cancel action"}, {"text": "Show main menu"}])
    return {
        "keyboard": rows,
        "resize_keyboard": True,
        "is_persistent": True,
    }


SUBSCRIBE_CATEGORY_KEYBOARD = _build_subscribe_category_keyboard()


def _build_rc_picker_keyboard() -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    for i in range(0, len(ALLOWED_RCS), 2):
        row: list[dict[str, str]] = [{"text": ALLOWED_RCS[i]}]
        if i + 1 < len(ALLOWED_RCS):
            row.append({"text": ALLOWED_RCS[i + 1]})
        rows.append(row)

    rows.append([{"text": "Cancel action"}, {"text": "Show main menu"}])
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

    rows.append([{"text": "Cancel action"}, {"text": "Show main menu"}])
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
    profile = repository.get_profile(user["id"])

    raw_text = text.strip()
    command = handle_text_or_command(raw_text)
    user_id = user["id"]

    if command in {"/start", "/menu", "/help"}:
        _clear_user_flow(user_id)
        if not profile or not profile.get("rc_name"):
            ONBOARDING_FLOWS[user_id] = {"step": "rc"}
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
        ONBOARDING_FLOWS[user_id] = {"step": "rc"}
        await send_message(chat["id"], "Please set your RC first.", RC_PICKER_KEYBOARD)
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

    if command == "/delete":
        await _start_delete_flow(chat["id"], user_id)
        return

    if user_id in ONBOARDING_FLOWS:
        await _continue_onboarding_flow(chat["id"], user_id, raw_text)
        return

    if user_id in CREATE_FLOWS:
        await _continue_create_flow(chat["id"], user_id, raw_text)
        return

    if user_id in EDIT_FLOWS:
        await _continue_edit_flow(chat["id"], user_id, raw_text)
        return

    if user_id in DELETE_FLOWS:
        await _continue_delete_flow(chat["id"], user_id, raw_text)
        return

    if user_id in PROFILE_FLOWS:
        await _continue_profile_flow(chat["id"], user_id, raw_text)
        return

    if user_id in SUBSCRIBE_FLOWS:
        await _continue_subscribe_flow(chat["id"], user_id, raw_text)
        return

    selected_category = _category_from_text(raw_text)
    if selected_category:
        if not profile or not profile.get("rc_name"):
            ONBOARDING_FLOWS[user_id] = {"step": "rc"}
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
            ONBOARDING_FLOWS[user_id] = {"step": "rc"}
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
            ONBOARDING_FLOWS[user_id] = {"step": "rc"}
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
        lines.append("\nTap 'Edit my event' below to update one.")
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
    await send_message(chat_id, f"Event created: {event['title']}", CREATED_FLOW_KEYBOARD)


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
    CREATE_FLOWS.pop(user_id, None)
    EDIT_FLOWS.pop(user_id, None)
    DELETE_FLOWS.pop(user_id, None)
    PROFILE_FLOWS.pop(user_id, None)
    ONBOARDING_FLOWS.pop(user_id, None)
    SUBSCRIBE_FLOWS.pop(user_id, None)


async def _continue_onboarding_flow(chat_id: int, user_id: str, text: str) -> None:
    value = text.strip()
    canonical = ALLOWED_RCS_MAP.get(value.lower())
    if not canonical:
        await send_message(chat_id, "Please pick one RC from the keyboard.", RC_PICKER_KEYBOARD)
        return
    repository.set_profile(user_id, None, canonical)
    ONBOARDING_FLOWS.pop(user_id, None)
    await send_message(chat_id, f"Great — RC set to {canonical}.", MAIN_MENU_KEYBOARD)


async def _start_profile_flow(chat_id: int, user_id: str) -> None:
    profile = repository.get_profile(user_id)
    PROFILE_FLOWS[user_id] = {"step": "name"}
    await send_message(
        chat_id,
        (
            f"Current profile:\n"
            f"Name: {profile['effective_display_name'] if profile else '-'}\n"
            f"RC: {profile.get('rc_name') if profile else '-'}\n\n"
            f"Step 1/2: Enter preferred name (or type 'skip')."
        ),
        FLOW_ACTIONS_KEYBOARD,
    )


async def _continue_profile_flow(chat_id: int, user_id: str, text: str) -> None:
    state = PROFILE_FLOWS.get(user_id)
    if not state:
        return

    value = text.strip()
    if not value:
        await send_message(chat_id, "Please enter a value.", FLOW_ACTIONS_KEYBOARD)
        return

    if state["step"] == "name":
        state["name"] = None if value.lower() in {"skip", "none"} else value[:80]
        state["step"] = "rc"
        await send_message(chat_id, "Step 2/2: Pick your RC.", RC_PICKER_KEYBOARD)
        return

    if state["step"] == "rc":
        canonical = ALLOWED_RCS_MAP.get(value.lower())
        if not canonical:
            await send_message(chat_id, "Please pick one RC from the keyboard.", RC_PICKER_KEYBOARD)
            return
        repository.set_profile(user_id, state.get("name"), canonical)
        PROFILE_FLOWS.pop(user_id, None)
        await send_message(chat_id, f"Profile updated. RC: {canonical}", MAIN_MENU_KEYBOARD)
        return


async def _start_subscribe_flow(chat_id: int, user_id: str) -> None:
    SUBSCRIBE_FLOWS[user_id] = {"step": "category"}
    await send_message(chat_id, "Choose a category to subscribe:", SUBSCRIBE_CATEGORY_KEYBOARD)


async def _continue_subscribe_flow(chat_id: int, user_id: str, text: str) -> None:
    value = text.strip()
    key = CATEGORY_NAME_TO_KEY.get(value.lower())
    if not key or key not in CATEGORY_KEYS:
        await send_message(chat_id, "Please pick a category from the keyboard.", SUBSCRIBE_CATEGORY_KEYBOARD)
        return

    repository.subscribe_category(user_id, key)
    SUBSCRIBE_FLOWS.pop(user_id, None)
    await send_message(chat_id, f"Subscribed to {category_label(key)}", LIST_FLOW_KEYBOARD)


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
        await send_message(chat_id, f"Event created: {event['title']}", CREATED_FLOW_KEYBOARD)


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

    EDIT_FLOWS[user_id] = {"step": "event_index", "data": {}, "index_map": index_map}
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

    if step == "event_index":
        event_id = state["index_map"].get(value)
        if not event_id:
            await send_message(chat_id, "Invalid event number. Choose one from the list above.", FLOW_ACTIONS_KEYBOARD)
            return
        data["event_id"] = event_id
        state["step"] = "field_choice"
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
            EDIT_FLOWS.pop(user_id, None)
            return

        ok, msg = repository.edit_event_fields(
            creator_user_id=user_id,
            event_id=data["event_id"],
            **kwargs,
        )
        EDIT_FLOWS.pop(user_id, None)
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

    DELETE_FLOWS[user_id] = {"step": "event_index", "data": {}, "index_map": index_map}
    await send_message(chat_id, "\n".join(lines), FLOW_ACTIONS_KEYBOARD)


async def _continue_delete_flow(chat_id: int, user_id: str, text: str) -> None:
    state = DELETE_FLOWS.get(user_id)
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
            DELETE_FLOWS.pop(user_id, None)
            return
        
        data["event_id"] = event_id
        data["event_title"] = event["title"]
        state["step"] = "confirm"
        await send_message(
            chat_id,
            f"⚠️ Are you sure you want to delete '{event['title']}'?\n\nAll participants will lose access to this event and reminders will be cancelled.\n\nType 'yes' to confirm or 'no' to cancel.",
            FLOW_ACTIONS_KEYBOARD,
        )
        return

    if step == "confirm":
        if value.lower() not in {"yes", "y"}:
            DELETE_FLOWS.pop(user_id, None)
            await send_message(chat_id, f"Deletion of '{data.get('event_title')}' cancelled.", CREATED_FLOW_KEYBOARD)
            return

        ok, msg = repository.delete_event(
            creator_user_id=user_id,
            event_id=data["event_id"],
        )
        DELETE_FLOWS.pop(user_id, None)
        await send_message(chat_id, msg if ok else f"Unable to delete event: {msg}", CREATED_FLOW_KEYBOARD)


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
    profile = repository.get_profile(user["id"])

    if data.startswith("cat:"):
        await answer_callback_query(query["id"])
        if not profile or not profile.get("rc_name"):
            ONBOARDING_FLOWS[user["id"]] = {"step": "rc"}
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
        if not profile or not profile.get("rc_name"):
            ONBOARDING_FLOWS[user["id"]] = {"step": "rc"}
            await send_message(chat["id"], "Set your RC first to manage subscriptions.", RC_PICKER_KEYBOARD)
            return
        category = data.split(":", 1)[1]
        repository.subscribe_category(user["id"], category)
        await answer_callback_query(query["id"], "Subscribed")
        await send_message(chat["id"], f"Subscribed to {category_label(category)}")
        return

    await answer_callback_query(query["id"])


async def _send_event_list(chat_id: int, category: str, page: int, viewer_rc: str | None) -> None:
    category_filter = None if category == "all" else category
    rows = repository.list_events(category=category_filter, page=page, viewer_rc=viewer_rc)

    if not rows:
        await send_message(chat_id, "No events found.")
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

    await send_message(chat_id, "\n".join(lines), {"inline_keyboard": keyboard})
    await send_message(chat_id, "Use the options below to continue.", LIST_FLOW_KEYBOARD)


def _subscription_buttons() -> list[list[dict[str, str]]]:
    rows: list[list[dict[str, str]]] = []
    for key in CATEGORY_KEYS:
        rows.append([{ "text": category_label(key), "callback_data": f"subc:{key}" }])
    return rows
