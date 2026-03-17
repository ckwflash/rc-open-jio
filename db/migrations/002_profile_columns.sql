alter table if exists users
  add column if not exists custom_display_name text,
  add column if not exists rc_name text;
