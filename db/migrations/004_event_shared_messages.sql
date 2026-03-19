create table if not exists event_shared_messages (
  id bigserial primary key,
  event_id uuid not null references events(id) on delete cascade,
  inline_message_id text not null unique,
  created_at timestamptz not null default now()
);

create index if not exists event_shared_messages_event_idx
  on event_shared_messages (event_id, created_at desc);
