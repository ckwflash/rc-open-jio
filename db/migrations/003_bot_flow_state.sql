create table if not exists bot_user_flows (
  id bigserial primary key,
  user_id uuid not null references users(id) on delete cascade,
  flow_type text not null,
  state jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  expires_at timestamptz not null default (now() + interval '2 hours'),
  unique (user_id, flow_type)
);

create index if not exists bot_user_flows_user_expires_idx
  on bot_user_flows (user_id, expires_at desc);

create index if not exists bot_user_flows_expires_idx
  on bot_user_flows (expires_at);
