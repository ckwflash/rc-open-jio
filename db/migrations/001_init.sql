create extension if not exists pgcrypto;

create type event_category as enum (
  'academic_study_skills',
  'career_internships',
  'wellness_mental_health',
  'sports_fitness',
  'arts_culture',
  'community_service_volunteering',
  'entrepreneurship_hackathons',
  'residential_college_life',
  'admin_deadlines',
  'social_networking',
  'other'
);

create type event_status as enum (
  'published',
  'cancelled'
);

create type participant_status as enum (
  'joined',
  'left'
);

create type subscription_kind as enum (
  'category',
  'creator'
);

create type notification_kind as enum (
  'reminder_24h',
  'reminder_1h',
  'event_update',
  'new_event_subscription'
);

create type notification_status as enum (
  'pending',
  'processing',
  'sent',
  'failed',
  'cancelled'
);

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  telegram_user_id bigint not null unique,
  telegram_handle text,
  telegram_display_name text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists events (
  id uuid primary key default gen_random_uuid(),
  creator_user_id uuid not null references users(id),
  title text not null,
  description text not null,
  category event_category not null,
  target_audience text not null default 'all_rc',
  start_at timestamptz not null,
  end_at timestamptz,
  location_text text not null,
  capacity integer check (capacity is null or capacity > 0),
  status event_status not null default 'published',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint events_time_chk check (end_at is null or end_at > start_at)
);

create table if not exists event_participants (
  event_id uuid not null references events(id) on delete cascade,
  user_id uuid not null references users(id) on delete cascade,
  status participant_status not null default 'joined',
  joined_at timestamptz not null default now(),
  last_notified_event_version integer not null default 0,
  primary key (event_id, user_id)
);

create table if not exists event_subscriptions (
  id bigserial primary key,
  subscriber_user_id uuid not null references users(id) on delete cascade,
  kind subscription_kind not null,
  category event_category,
  creator_user_id uuid references users(id) on delete cascade,
  created_at timestamptz not null default now(),
  constraint subscription_target_chk check (
    (kind = 'category' and category is not null and creator_user_id is null)
    or
    (kind = 'creator' and creator_user_id is not null and category is null)
  )
);

create unique index if not exists event_subscriptions_category_unique
on event_subscriptions(subscriber_user_id, category)
where kind = 'category';

create unique index if not exists event_subscriptions_creator_unique
on event_subscriptions(subscriber_user_id, creator_user_id)
where kind = 'creator';

create table if not exists notification_outbox (
  id bigserial primary key,
  recipient_user_id uuid not null references users(id) on delete cascade,
  event_id uuid references events(id) on delete cascade,
  kind notification_kind not null,
  payload jsonb not null default '{}'::jsonb,
  scheduled_for timestamptz not null,
  status notification_status not null default 'pending',
  attempt_count integer not null default 0,
  max_attempts integer not null default 5,
  locked_at timestamptz,
  locked_by text,
  last_error text,
  dedupe_key text unique,
  created_at timestamptz not null default now(),
  sent_at timestamptz
);

create index if not exists events_start_at_idx on events(start_at);
create index if not exists events_category_start_at_idx on events(category, start_at);
create index if not exists events_creator_created_at_idx on events(creator_user_id, created_at desc);
create index if not exists event_participants_user_joined_idx on event_participants(user_id, joined_at desc);
create index if not exists event_participants_event_status_idx on event_participants(event_id, status);
create index if not exists notification_outbox_status_schedule_idx on notification_outbox(status, scheduled_for);

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger users_set_updated_at
before update on users
for each row execute function set_updated_at();

create trigger events_set_updated_at
before update on events
for each row execute function set_updated_at();
