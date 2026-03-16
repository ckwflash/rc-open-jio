# RC Open Jio (Telegram Bot MVP)

Telegram bot MVP for NUS Residential Colleges to create and join student events.

## Stack
- Python + FastAPI (Vercel serverless)
- Supabase Postgres
- Telegram Bot API

## Implemented MVP scope
- Browse events with category filters
- Create event
- View event details + participants
- Join event
- View joined events
- View created events
- Edit created event schedule/location
- Subscribe to category
- Subscribe to creator
- Notification queue with reminders:
  - 24h + 1h before event
  - fallback to 1h only when event is <24h away
  - regenerate reminders when event time changes

## Privacy behavior implemented
- Participants can see:
  - creator display name + Telegram handle
  - participant display names only
- Event creator can see:
  - participant display names + Telegram handles

## Categories (fixed)
- academic_study_skills
- career_internships
- wellness_mental_health
- sports_fitness
- arts_culture
- community_service_volunteering
- entrepreneurship_hackathons
- residential_college_life
- admin_deadlines
- social_networking
- other

## Project structure
- `api/webhook.py` Telegram webhook entrypoint (`/api/webhook`)
- `api/cron.py` notification dispatcher (`/api/cron`)
- `app/bot.py` bot command + callback handlers
- `app/repository.py` database operations
- `app/notifications.py` queue dispatch logic
- `db/migrations/001_init.sql` schema

## Environment
Copy `.env.example` to `.env` and fill values:
- `BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `DATABASE_URL`
- `CRON_SECRET`
- `DEFAULT_TIMEZONE` (default: `Asia/Singapore`)

## Database setup
Run `db/migrations/001_init.sql` against your Supabase Postgres.

For local Postgres testing (resettable schema), use:
- `db/local/001_local_init.sql`

This local file is for development reset only. Keep Supabase migration history based on:
- `db/migrations/001_init.sql`

## Local run
Install dependencies:
- `pip install -r requirements.txt`

Run webhook function locally:
- `uvicorn api.webhook:app --reload --port 8000`

Run cron function locally:
- `uvicorn api.cron:app --reload --port 8001`

## Dev mode (no cron)
For local feature testing without reminder dispatch:

1. In `.env`, set:
  - `DEV_MODE=true`
  - `DATABASE_URL` to local Postgres
2. Apply local schema using:
  - `db/local/001_local_init.sql`
3. Start only webhook server:
  - `uvicorn api.webhook:app --reload --port 8000`
4. Set Telegram webhook to your local tunnel URL (`/api/webhook` path when deployed, `/` for direct local uvicorn endpoint).

Notes:
- In `DEV_MODE=true`, webhook secret header check is disabled for local testing.
- You can skip running `api/cron.py` in this mode.

## Local Postgres with Docker
Use this when you want a temporary, local test database.

1. Install Docker Engine + Docker Compose plugin on your machine.
2. Start DB + apply schema in one command:
  - `./scripts/local_db_setup.sh`

This uses:
- [docker-compose.local.yml](docker-compose.local.yml)
- [db/local/001_local_init.sql](db/local/001_local_init.sql)

Stop/remove the local DB:
- `docker compose -f docker-compose.local.yml down`

Stop/remove DB + delete data volume:
- `docker compose -f docker-compose.local.yml down -v`

## Webhook setup (local)
Telegram must reach your local webhook via a public HTTPS URL.

1. Start webhook server:
  - `uvicorn api.webhook:app --reload --port 8000`
2. Start a tunnel to your local port 8000 (choose one):
  - ngrok: `ngrok http 8000`
  - cloudflared: `cloudflared tunnel --url http://localhost:8000`
3. Copy the HTTPS URL from tunnel output, then set env and register webhook:
  - `export WEBHOOK_URL=https://<tunnel-domain>/`
  - `python scripts/set_webhook.py`
4. Verify webhook registration:
  - Open `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo`

Note:
- When running directly with `uvicorn api.webhook:app`, the webhook endpoint is `/`.
- On Vercel deployment, the webhook endpoint is `/api/webhook`.

## Telegram setup
Set your bot webhook URL to your deployment path:
- `https://<your-app>/api/webhook`

Set Telegram webhook secret token to match `TELEGRAM_WEBHOOK_SECRET`.

## Commands
- `/start`
- `/menu`
- `/list`
- `/create`
- `/edit`
- `/joined`
- `/created`
- `/subscribe`

### `/create` format
`/create Title | CategoryKey | TargetAudience | YYYY-MM-DD HH:MM | Location | Capacity | Description`

Example:
`/create Badminton @ USC | sports_fitness | all_rc | 2026-03-20 19:30 | USC Hall | 12 | Casual doubles play`

### `/edit` format
`/edit EventID | YYYY-MM-DD HH:MM | New Location`
