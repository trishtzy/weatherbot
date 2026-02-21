import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DGS_API_KEY = os.environ.get("DGS_API_KEY", "")

WEATHER_API_URL = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"

DB_PATH = "subscribers.db"

FORECAST_EMOJI = {
    "Fair": "☀️",
    "Fair (Day)": "☀️",
    "Fair (Night)": "🌙",
    "Fair and Warm": "🌤️",
    "Partly Cloudy": "⛅",
    "Partly Cloudy (Day)": "⛅",
    "Partly Cloudy (Night)": "☁️",
    "Cloudy": "☁️",
    "Hazy": "🌫️",
    "Slightly Hazy": "🌫️",
    "Windy": "💨",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Light Rain": "🌦️",
    "Moderate Rain": "🌧️",
    "Heavy Rain": "🌧️",
    "Passing Showers": "🌦️",
    "Light Showers": "🌦️",
    "Showers": "🌧️",
    "Heavy Showers": "🌧️",
    "Thundery Showers": "⛈️",
    "Heavy Thundery Showers": "⛈️",
    "Heavy Thundery Showers with Gusty Winds": "🌪️",
}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def init_db():
    """Initialize database by running pending migrations using PRAGMA user_version."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get current database version
    current_version, = cursor.execute("PRAGMA user_version").fetchone() or (0,)

    # If the subscribers table already exists but user_version is 0,
    # the initial schema (0001) was applied before the migration system existed.
    # Stamp it at version 1 so it won't be re-applied.
    if current_version == 0:
        table_exists = cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='subscribers'"
        ).fetchone()
        if table_exists:
            cursor.execute("PRAGMA user_version=1")
            conn.commit()
            current_version = 1
            logger.info("Existing database detected, stamped at version 1")

    # Load and sort migration files
    if not os.path.exists(MIGRATIONS_DIR):
        logger.warning("Migrations directory not found: %s", MIGRATIONS_DIR)
        conn.close()
        return

    migration_files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")])

    for migration_file in migration_files:
        # Extract version number from filename (000N_*.sql)
        try:
            migration_version = int(migration_file.split("_")[0])
        except (IndexError, ValueError):
            logger.warning("Skipping invalid migration file: %s", migration_file)
            continue

        # Skip if already applied
        if migration_version <= current_version:
            logger.debug("Migration %d already applied", migration_version)
            continue

        # Apply migration
        migration_path = os.path.join(MIGRATIONS_DIR, migration_file)
        with open(migration_path, "r") as f:
            sql = f.read()
        
        try:
            logger.info("Applying migration %d: %s", migration_version, migration_file)
            cursor.executescript(sql)
            conn.commit()
            logger.info("Database now at version %d", migration_version)
        except Exception as e:
            logger.error("Failed to apply migration %d: %s", migration_version, e)
            conn.rollback()
            raise
    
    conn.close()
    logger.info("Database initialization complete")


def add_subscriber(chat_id: int, area: str) -> bool:
    """Add a subscription. Returns True if a new row was inserted, False if already existed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT OR IGNORE INTO subscribers (chat_id, area) VALUES (?, ?)",
        (chat_id, area),
    )
    conn.commit()
    inserted = cursor.rowcount > 0
    conn.close()
    return inserted


def remove_subscriber(chat_id: int, area: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "DELETE FROM subscribers WHERE chat_id = ? AND area = ?",
        (chat_id, area),
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_subscriptions(chat_id: int) -> list[str]:
    """Return all subscribed area names for a chat."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT area FROM subscribers WHERE chat_id = ? ORDER BY area", (chat_id,)
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_all_subscribers():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT chat_id, area FROM subscribers").fetchall()
    conn.close()
    return rows


def update_subscriber_timestamps(chat_id: int, area: str, last_sent_at: str, next_scheduled_at: str):
    """Update the last_sent_at and next_scheduled_at timestamps for a subscriber."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE subscribers SET last_sent_at = ?, next_scheduled_at = ? WHERE chat_id = ? AND area = ?",
        (last_sent_at, next_scheduled_at, chat_id, area),
    )
    conn.commit()
    conn.close()


def get_overdue_subscribers(now_iso: str) -> list[tuple[int, str]]:
    """Get subscribers whose next_scheduled_at is due (<= now)."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT chat_id, area FROM subscribers WHERE next_scheduled_at IS NULL OR next_scheduled_at <= ?",
        (now_iso,),
    ).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Weather API
# ---------------------------------------------------------------------------

_forecast_cache: dict | None = None
_forecast_cache_expiry: datetime | None = None


def _get_forecast_expiry(data: dict) -> datetime | None:
    """Extract the valid_period end time from forecast data."""
    items = data.get("items", [])
    if not items:
        return None
    end = items[-1].get("valid_period", {}).get("end")
    if end:
        return datetime.fromisoformat(end)
    return None


async def fetch_forecast() -> dict | None:
    """Fetch the 2-hour forecast, returning a cached response if still fresh."""
    global _forecast_cache, _forecast_cache_expiry
    if _forecast_cache and _forecast_cache_expiry and datetime.now(timezone.utc) < _forecast_cache_expiry:
        return _forecast_cache

    headers = {}
    if DGS_API_KEY:
        headers["x-api-key"] = DGS_API_KEY

    async with httpx.AsyncClient() as client:
        resp = await client.get(WEATHER_API_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

    if data.get("code") != 0:
        logger.error("Weather API error: %s", data.get("errorMsg"))
        return None

    result = data.get("data")
    _forecast_cache = result
    _forecast_cache_expiry = _get_forecast_expiry(result) if result else None
    return _forecast_cache


def find_area_forecast(data: dict, area: str) -> str | None:
    items = data.get("items", [])
    if not items:
        return None
    latest = items[-1]
    for fc in latest.get("forecasts", []):
        if fc["area"].lower() == area.lower():
            return fc["forecast"]
    return None


def get_valid_period_text(data: dict) -> str:
    items = data.get("items", [])
    if not items:
        return ""
    latest = items[-1]
    vp = latest.get("valid_period", {})
    return vp.get("text", "")


def get_validity_timestamps(data: dict) -> tuple[str | None, str | None]:
    """Extract validity period start and end from forecast data in UTC ISO format."""
    items = data.get("items", [])
    if not items:
        return None, None
    latest = items[-1]
    vp = latest.get("valid_period", {})
    start_str = vp.get("start")
    end_str = vp.get("end")
    if start_str and end_str:
        # Parse with explicit Singapore timezone and convert to UTC
        start_dt = datetime.fromisoformat(start_str).replace(tzinfo=ZoneInfo("Asia/Singapore"))
        end_dt = datetime.fromisoformat(end_str).replace(tzinfo=ZoneInfo("Asia/Singapore"))
        start_utc = start_dt.astimezone(timezone.utc)
        end_utc = end_dt.astimezone(timezone.utc)
        return start_utc.isoformat(), end_utc.isoformat()
    return None, None


def calculate_next_scheduled_time(current_time: datetime) -> str:
    """Calculate next scheduled time.
    
    Rounds current time down to nearest :30 and adds 2 hours.
    This creates validity windows like 12:30am-2:30am, 2:30am-4:30am, etc.
    """
    # Round down to nearest :30
    if current_time.minute >= 30:
        rounded = current_time.replace(minute=30, second=0, microsecond=0)
    else:
        rounded = current_time.replace(minute=0, second=0, microsecond=0) - timedelta(minutes=30)
    
    # Add 2 hours to get to the start of the next window
    next_scheduled = rounded + timedelta(hours=2)
    return next_scheduled.isoformat()


def get_all_area_names(data: dict) -> list[str]:
    return sorted(m["name"] for m in data.get("area_metadata", []))


# Cache for area names (unlikely to change often)
_area_names_cache: list[str] = []
_area_names_cache_time: float = 0
_AREA_NAMES_TTL = 86400  # 24 hours


async def get_cached_area_names() -> list[str] | None:
    """Return cached area names, refreshing from the API if stale."""
    global _area_names_cache, _area_names_cache_time
    if _area_names_cache and (time.monotonic() - _area_names_cache_time) < _AREA_NAMES_TTL:
        return _area_names_cache
    data = await fetch_forecast()
    if data is None:
        return _area_names_cache or None
    _area_names_cache = get_all_area_names(data)
    _area_names_cache_time = time.monotonic()
    return _area_names_cache


def format_forecast_message(area: str, forecast: str, valid_period: str) -> str:
    emoji = FORECAST_EMOJI.get(forecast, "")
    lines = [
        f"{emoji} *{area}*",
        f"Forecast: *{forecast}*",
    ]
    if valid_period:
        lines.append(f"Valid: {valid_period}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Bot command handlers
# ---------------------------------------------------------------------------

HELP_TEXT = (
    "Commands:\n"
    "/subscribe <area> - Get 2-hourly weather updates (multiple areas OK)\n"
    "/unsubscribe <area> - Stop updates for an area\n"
    "/weather - Current forecast for your subscribed areas\n"
    "/areas - List all available areas\n"
    "/help - Show this message\n\n"
    "Example: /subscribe Bedok"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm the SG Weather Bot.\n\n" + HELP_TEXT)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def cmd_areas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    names = await get_cached_area_names()
    if names is None:
        await update.message.reply_text("Sorry, could not fetch area list right now.")
        return
    text = "Available areas:\n\n" + "\n".join(f"• {n}" for n in names)
    await update.message.reply_text(text)


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Please provide an area name.\n"
            "Example: /subscribe Bedok\n\n"
            "Use /areas to see the full list."
        )
        return

    area_input = " ".join(context.args)

    # Validate the area exists using cached names
    names = await get_cached_area_names()
    if names is None:
        await update.message.reply_text("Sorry, could not reach the weather service right now. Try again later.")
        return

    # Case-insensitive match
    valid_areas = {name.lower(): name for name in names}
    matched_area = valid_areas.get(area_input.lower())

    if matched_area is None:
        await update.message.reply_text(
            f"Area \"{area_input}\" not found.\n"
            "Use /areas to see available areas."
        )
        return

    inserted = add_subscriber(update.effective_chat.id, matched_area)

    if not inserted:
        await update.message.reply_text(f"You're already subscribed to *{matched_area}*.", parse_mode="Markdown")
        return

    # Fetch current forecast for the confirmation message
    data = await fetch_forecast()
    reply = f"Subscribed to weather updates for *{matched_area}*! You'll receive forecasts every 2 hours."
    
    now = datetime.now(timezone.utc)
    next_scheduled = None
    
    if data:
        forecast = find_area_forecast(data, matched_area)
        valid_period = get_valid_period_text(data)
        if forecast:
            reply += "\n\nCurrent forecast:\n" + format_forecast_message(matched_area, forecast, valid_period)
        
        # Calculate next scheduled time based on current time (not API validity)
        next_scheduled = calculate_next_scheduled_time(now)
    
    await update.message.reply_text(reply, parse_mode="Markdown")
    
    # Update timestamps for the new subscriber
    if next_scheduled:
        update_subscriber_timestamps(update.effective_chat.id, matched_area, now.isoformat(), next_scheduled)


async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        areas = get_subscriptions(update.effective_chat.id)
        if not areas:
            await update.message.reply_text("You have no active subscriptions.")
        else:
            listing = "\n".join(f"• {a}" for a in areas)
            await update.message.reply_text(
                "Please specify an area to unsubscribe from.\n"
                f"Example: /unsubscribe {areas[0]}\n\n"
                f"Your subscriptions:\n{listing}"
            )
        return

    area_input = " ".join(context.args)

    # Case-insensitive match against user's own subscriptions
    areas = get_subscriptions(update.effective_chat.id)
    sub_map = {a.lower(): a for a in areas}
    matched_area = sub_map.get(area_input.lower())

    if matched_area is None:
        await update.message.reply_text(
            f"You're not subscribed to \"{area_input}\".\n"
            "Use /unsubscribe with no arguments to see your subscriptions."
        )
        return

    remove_subscriber(update.effective_chat.id, matched_area)
    await update.message.reply_text(f"Unsubscribed from *{matched_area}*.", parse_mode="Markdown")


async def cmd_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    areas = get_subscriptions(update.effective_chat.id)
    if not areas:
        await update.message.reply_text(
            "You're not subscribed yet.\n"
            "Use /subscribe <area> to get started."
        )
        return

    data = await fetch_forecast()
    if data is None:
        await update.message.reply_text("Sorry, could not fetch the forecast right now.")
        return

    valid_period = get_valid_period_text(data)
    messages = []
    for area in areas:
        forecast = find_area_forecast(data, area)
        if forecast:
            messages.append(format_forecast_message(area, forecast, valid_period))

    if not messages:
        await update.message.reply_text("No forecast data available for your areas right now.")
        return

    await update.message.reply_text("\n\n".join(messages), parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Scheduled job: push forecasts to all subscribers
# ---------------------------------------------------------------------------

async def send_scheduled_updates(app: Application, startup: bool = False):
    """Send forecasts to subscribers whose next_scheduled_at is due.
    
    Args:
        app: The Telegram bot application
        startup: If True, only send if current forecast is still valid
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    
    # Get current forecast data
    data = await fetch_forecast()
    if data is None:
        if not startup:
            logger.warning("Scheduled update: could not fetch forecast")
        return
    
    # Get validity period in UTC
    validity_start, validity_end = get_validity_timestamps(data)
    if not validity_start or not validity_end:
        logger.warning("Scheduled update: could not extract validity period")
        return
    
    # On startup, only send if current forecast is still valid (not expired)
    if startup:
        if now >= datetime.fromisoformat(validity_end):
            logger.info("Startup: current forecast expired, waiting for next scheduled run")
            return
    
    # Get subscribers who need an update
    subscribers = get_overdue_subscribers(now_iso)
    if not subscribers:
        return
    
    valid_period = get_valid_period_text(data)
    next_scheduled = calculate_next_scheduled_time(now)
    
    for chat_id, area in subscribers:
        forecast = find_area_forecast(data, area)
        if forecast is None:
            continue
        
        text = format_forecast_message(area, forecast, valid_period)
        try:
            await app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
            # Update timestamps after successful send
            update_subscriber_timestamps(chat_id, area, validity_start, next_scheduled)
            logger.info("Sent forecast to chat_id=%s for area=%s, next scheduled: %s", 
                        chat_id, area, next_scheduled)
        except Exception:
            logger.exception("Failed to send update to chat_id=%s", chat_id)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def make_post_init():
    async def post_init(app: Application):
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            send_scheduled_updates,
            trigger="interval",
            minutes=1,  # Check every minute for due subscribers
            args=[app],
            id="forecast_scheduler",
            replace_existing=True,
        )
        scheduler.start()
        
        # Check for overdue subscribers on startup
        logger.info("Running startup check for overdue subscribers...")
        await send_scheduled_updates(app, startup=True)
    return post_init


def main():
    init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(make_post_init()).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("areas", cmd_areas))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    app.add_handler(CommandHandler("weather", cmd_weather))

    logger.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
