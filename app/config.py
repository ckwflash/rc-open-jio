from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    bot_token: str
    webhook_secret: str
    database_url: str
    cron_secret: str
    default_timezone: str
    dev_mode: bool


settings = Settings(
    bot_token=getenv("BOT_TOKEN", ""),
    webhook_secret=getenv("TELEGRAM_WEBHOOK_SECRET", ""),
    database_url=getenv("DATABASE_URL", ""),
    cron_secret=getenv("CRON_SECRET", ""),
    default_timezone=getenv("DEFAULT_TIMEZONE", "Asia/Singapore"),
    dev_mode=_parse_bool(getenv("DEV_MODE", "false")),
)
