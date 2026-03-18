from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.config import settings
from app.constants import ALLOWED_RCS_MAP, CATEGORY_KEYS
from app.db import get_conn

PAGE_SIZE = 8


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def upsert_user(telegram_user_id: int, telegram_handle: str | None, display_name: str) -> dict[str, Any]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into users (telegram_user_id, telegram_handle, telegram_display_name)
            values (%s, %s, %s)
            on conflict (telegram_user_id)
            do update set
              telegram_handle = excluded.telegram_handle,
              telegram_display_name = excluded.telegram_display_name,
              updated_at = now()
            returning *
            """,
            (telegram_user_id, telegram_handle, display_name),
        )
        row = cur.fetchone()
        conn.commit()
        return row


def create_event(
    creator_user_id: str,
    title: str,
    description: str,
    category: str,
    target_audience: str,
    start_at: datetime,
    location_text: str,
    capacity: int | None,
) -> dict[str, Any]:
    if category not in CATEGORY_KEYS:
        raise ValueError("Invalid category")

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into events (creator_user_id, title, description, category, target_audience, start_at, location_text, capacity)
            values (%s, %s, %s, %s, %s, %s, %s, %s)
            returning *
            """,
            (creator_user_id, title, description, category, target_audience, start_at, location_text, capacity),
        )
        event = cur.fetchone()

        cur.execute(
            """
            insert into event_participants (event_id, user_id, status)
            values (%s, %s, 'joined')
            on conflict (event_id, user_id) do update set status = 'joined', joined_at = now()
            """,
            (event["id"], creator_user_id),
        )
        _rebuild_reminder_jobs(cur, event["id"], creator_user_id, start_at)

        cur.execute(
            """
            insert into notification_outbox (recipient_user_id, event_id, kind, payload, scheduled_for, dedupe_key)
            select
                s.subscriber_user_id,
                %s::uuid,
                'new_event_subscription',
                jsonb_build_object('title', %s::text, 'category', %s::text),
                now(),
                concat('new_event_subscription:', s.subscriber_user_id::text, ':', %s::uuid::text)
            from event_subscriptions s
            where (s.kind = 'category' and s.category = %s::event_category)
               or (s.kind = 'creator' and s.creator_user_id = %s::uuid)
            on conflict (dedupe_key) do nothing
            """,
            (
                event["id"],
                event["title"],
                event["category"],
                event["id"],
                event["category"],
                event["creator_user_id"],
            ),
        )

        conn.commit()
        return event


def list_events(category: str | None = None, page: int = 0, viewer_rc: str | None = None) -> list[dict[str, Any]]:
    offset = page * PAGE_SIZE
    with get_conn() as conn, conn.cursor() as cur:
        if category and category in CATEGORY_KEYS:
            cur.execute(
                """
                select
                  e.*,
                                    coalesce(u.custom_display_name, u.telegram_display_name) as creator_name,
                  u.telegram_handle as creator_handle,
                  coalesce(sum(case when ep.status = 'joined' then 1 else 0 end), 0)::int as participant_count
                from events e
                join users u on u.id = e.creator_user_id
                left join event_participants ep on ep.event_id = e.id
                                where e.status = 'published'
                                    and e.start_at >= now()
                                    and e.category = %s
                                    and (
                                                lower(e.target_audience) in ('all', 'all_rc', 'everyone')
                                                or (%s::text is not null and lower(e.target_audience) = lower(%s::text))
                                            )
                group by e.id, u.custom_display_name, u.telegram_display_name, u.telegram_handle
                order by e.start_at asc
                limit %s offset %s
                """,
                                (category, viewer_rc, viewer_rc, PAGE_SIZE, offset),
            )
        else:
            cur.execute(
                """
                select
                  e.*,
                                    coalesce(u.custom_display_name, u.telegram_display_name) as creator_name,
                  u.telegram_handle as creator_handle,
                  coalesce(sum(case when ep.status = 'joined' then 1 else 0 end), 0)::int as participant_count
                from events e
                join users u on u.id = e.creator_user_id
                left join event_participants ep on ep.event_id = e.id
                                where e.status = 'published'
                                    and e.start_at >= now()
                                    and (
                                                lower(e.target_audience) in ('all', 'all_rc', 'everyone')
                                                or (%s::text is not null and lower(e.target_audience) = lower(%s::text))
                                            )
                group by e.id, u.custom_display_name, u.telegram_display_name, u.telegram_handle
                order by e.start_at asc
                limit %s offset %s
                """,
                                (viewer_rc, viewer_rc, PAGE_SIZE, offset),
            )
        return cur.fetchall()


def get_event(event_id: str) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select
              e.*,
                            coalesce(u.custom_display_name, u.telegram_display_name) as creator_name,
              u.telegram_handle as creator_handle
            from events e
            join users u on u.id = e.creator_user_id
            where e.id = %s
            """,
            (event_id,),
        )
        return cur.fetchone()


def get_event_participants(event_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select
              ep.user_id,
                            coalesce(u.custom_display_name, u.telegram_display_name) as display_name,
              u.telegram_handle,
              ep.joined_at
            from event_participants ep
            join users u on u.id = ep.user_id
            where ep.event_id = %s and ep.status = 'joined'
            order by ep.joined_at asc
            """,
            (event_id,),
        )
        return cur.fetchall()


def join_event(event_id: str, user_id: str) -> tuple[bool, str]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select * from events where id = %s and status = 'published' for update", (event_id,))
        event = cur.fetchone()
        if not event:
            conn.rollback()
            return False, "Event not found or unavailable."

        cur.execute(
            "select count(*)::int as c from event_participants where event_id = %s and status = 'joined'",
            (event_id,),
        )
        count = cur.fetchone()["c"]
        if event["capacity"] is not None and count >= event["capacity"]:
            conn.rollback()
            return False, "Event is full."

        cur.execute(
            """
            insert into event_participants (event_id, user_id, status)
            values (%s, %s, 'joined')
            on conflict (event_id, user_id)
            do update set status = 'joined', joined_at = now()
            """,
            (event_id, user_id),
        )

        _rebuild_reminder_jobs(cur, event_id, user_id, event["start_at"])  # type: ignore[arg-type]

        conn.commit()
        return True, "You have joined this event."


def rebuild_all_reminders_for_event(event_id: str) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select start_at from events where id = %s", (event_id,))
        event = cur.fetchone()
        if not event:
            conn.rollback()
            return

        cur.execute(
            "select user_id from event_participants where event_id = %s and status = 'joined'",
            (event_id,),
        )
        participants = cur.fetchall()
        for row in participants:
            _rebuild_reminder_jobs(cur, event_id, row["user_id"], event["start_at"])  # type: ignore[arg-type]

        conn.commit()


def _rebuild_reminder_jobs(cur: Any, event_id: str, user_id: str, start_at: datetime) -> None:
    cur.execute(
        """
        delete from notification_outbox
        where event_id = %s
          and recipient_user_id = %s
          and kind in ('reminder_24h', 'reminder_1h')
          and status in ('pending', 'processing')
        """,
        (event_id, user_id),
    )

    now = now_utc()
    at_24h = start_at - timedelta(hours=24)
    at_1h = start_at - timedelta(hours=1)

    if at_24h > now:
        cur.execute(
            """
            insert into notification_outbox (recipient_user_id, event_id, kind, scheduled_for, dedupe_key)
            values (%s, %s, 'reminder_24h', %s, %s)
            on conflict (dedupe_key) do nothing
            """,
            (user_id, event_id, at_24h, f"reminder_24h:{event_id}:{user_id}:{int(start_at.timestamp())}"),
        )

    if at_1h > now:
        cur.execute(
            """
            insert into notification_outbox (recipient_user_id, event_id, kind, scheduled_for, dedupe_key)
            values (%s, %s, 'reminder_1h', %s, %s)
            on conflict (dedupe_key) do nothing
            """,
            (user_id, event_id, at_1h, f"reminder_1h:{event_id}:{user_id}:{int(start_at.timestamp())}"),
        )


def list_joined_events(user_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select e.*
            from event_participants ep
            join events e on e.id = ep.event_id
            where ep.user_id = %s and ep.status = 'joined'
            order by e.start_at asc
            """,
            (user_id,),
        )
        return cur.fetchall()


def list_created_events(creator_user_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select *
            from events
            where creator_user_id = %s
            order by start_at asc
            """,
            (creator_user_id,),
        )
        return cur.fetchall()


def edit_event_schedule_location(
    creator_user_id: str,
    event_id: str,
    start_at: datetime,
    location_text: str,
) -> tuple[bool, str]:
    return edit_event_fields(
        creator_user_id=creator_user_id,
        event_id=event_id,
        start_at=start_at,
        location_text=location_text,
    )


def edit_event_fields(
    creator_user_id: str,
    event_id: str,
    title: str | None = None,
    description: str | None = None,
    category: str | None = None,
    target_audience: str | None = None,
    start_at: datetime | None = None,
    location_text: str | None = None,
    capacity: int | None = None,
) -> tuple[bool, str]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select *
            from events
            where id = %s and creator_user_id = %s and status = 'published'
            for update
            """,
            (event_id, creator_user_id),
        )
        current_event = cur.fetchone()
        if not current_event:
            conn.rollback()
            return False, "Event not found, unavailable, or you are not the creator."

        if category is not None and category not in CATEGORY_KEYS:
            conn.rollback()
            return False, "Invalid category."
        if capacity is not None and capacity != -1 and capacity <= 0:
            conn.rollback()
            return False, "Capacity must be a positive number, or none."

        if target_audience is not None:
            lower_audience = target_audience.lower()
            if lower_audience not in {"all", "all_rc", "everyone"} and lower_audience not in ALLOWED_RCS_MAP:
                conn.rollback()
                return False, "Invalid target audience."
            if lower_audience in ALLOWED_RCS_MAP:
                target_audience = ALLOWED_RCS_MAP[lower_audience]
            elif lower_audience in {"all", "everyone"}:
                target_audience = "all_rc"

        next_title = title or current_event["title"]
        next_description = description or current_event["description"]
        next_category = category or current_event["category"]
        next_target_audience = target_audience or current_event["target_audience"]
        next_start_at = start_at or current_event["start_at"]
        next_location = location_text or current_event["location_text"]
        if capacity == -1:
            next_capacity = None
        else:
            next_capacity = current_event["capacity"] if capacity is None else capacity
        time_changed = next_start_at != current_event["start_at"]

        cur.execute(
            """
            update events
            set title = %s,
                description = %s,
                category = %s,
                target_audience = %s,
                start_at = %s,
                location_text = %s,
                capacity = %s,
                updated_at = now()
            where id = %s and creator_user_id = %s and status = 'published'
            returning *
            """,
            (
                next_title,
                next_description,
                next_category,
                next_target_audience,
                next_start_at,
                next_location,
                next_capacity,
                event_id,
                creator_user_id,
            ),
        )
        event = cur.fetchone()

        cur.execute(
            """
            select user_id
            from event_participants
            where event_id = %s and status = 'joined'
            """,
            (event_id,),
        )
        participants = cur.fetchall()

        for participant in participants:
            user_id = participant["user_id"]
            if time_changed:
                _rebuild_reminder_jobs(cur, event_id, user_id, next_start_at)
            cur.execute(
                """
                insert into notification_outbox (recipient_user_id, event_id, kind, payload, scheduled_for, dedupe_key)
                values (%s, %s, 'event_update', jsonb_build_object('reason', 'schedule_or_location_changed'), now(), %s)
                on conflict (dedupe_key) do nothing
                """,
                (
                    user_id,
                    event_id,
                    f"event_update:{event_id}:{user_id}:{int(next_start_at.timestamp())}:{next_location}",
                ),
            )

        conn.commit()
        return True, "Event updated and participants were notified."


def subscribe_category(subscriber_user_id: str, category: str) -> None:
    if category not in CATEGORY_KEYS:
        raise ValueError("Invalid category")

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into event_subscriptions (subscriber_user_id, kind, category)
            values (%s, 'category', %s)
            on conflict do nothing
            """,
            (subscriber_user_id, category),
        )
        conn.commit()


def subscribe_creator(subscriber_user_id: str, creator_user_id: str) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into event_subscriptions (subscriber_user_id, kind, creator_user_id)
            values (%s, 'creator', %s)
            on conflict do nothing
            """,
            (subscriber_user_id, creator_user_id),
        )
        conn.commit()


def set_profile(user_id: str, custom_display_name: str | None, rc_name: str | None) -> dict[str, Any] | None:
    normalized_rc: str | None = None
    if rc_name:
        rc_candidate = rc_name.strip().lower()
        if rc_candidate not in ALLOWED_RCS_MAP:
            raise ValueError("Invalid RC. Allowed: Tembusu, CAPT, RC4, RVRC")
        normalized_rc = ALLOWED_RCS_MAP[rc_candidate]

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            update users
            set custom_display_name = %s,
                rc_name = %s,
                updated_at = now()
            where id = %s
            returning *
            """,
            (custom_display_name, normalized_rc, user_id),
        )
        row = cur.fetchone()
        conn.commit()
        return row


def get_profile(user_id: str) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select
              id,
              telegram_display_name,
              custom_display_name,
              coalesce(custom_display_name, telegram_display_name) as effective_display_name,
              rc_name,
              telegram_handle
            from users
            where id = %s
            """,
            (user_id,),
        )
        return cur.fetchone()


def claim_due_notifications(limit: int = 50, locker: str = "cron") -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            with due as (
                select id
                from notification_outbox
                where status = 'pending' and scheduled_for <= now()
                order by scheduled_for asc
                limit %s
                for update skip locked
            )
            update notification_outbox n
            set status = 'processing', locked_at = now(), locked_by = %s
            where n.id in (select id from due)
            returning n.*
            """,
            (limit, locker),
        )
        rows = cur.fetchall()
        conn.commit()
        return rows


def mark_notification_sent(notification_id: int) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            update notification_outbox
            set status = 'sent', sent_at = now(), locked_at = null, locked_by = null
            where id = %s
            """,
            (notification_id,),
        )
        conn.commit()


def mark_notification_failed(notification_id: int, error: str) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            update notification_outbox
            set
              attempt_count = attempt_count + 1,
              status = case when attempt_count + 1 >= max_attempts then 'failed' else 'pending' end,
              scheduled_for = case when attempt_count + 1 >= max_attempts then scheduled_for else now() + interval '5 minutes' end,
              last_error = %s,
              locked_at = null,
              locked_by = null
            where id = %s
            """,
            (error[:500], notification_id),
        )
        conn.commit()


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select * from users where id = %s", (user_id,))
        return cur.fetchone()


def get_user_by_telegram_id(telegram_user_id: int) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select * from users where telegram_user_id = %s", (telegram_user_id,))
        return cur.fetchone()


def get_event_for_notification(event_id: str) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select id, title, start_at, location_text from events where id = %s", (event_id,))
        return cur.fetchone()


def format_dt(dt: datetime) -> str:
    tz = ZoneInfo(settings.default_timezone)
    return dt.astimezone(tz).strftime("%d %b %Y, %I:%M %p")
