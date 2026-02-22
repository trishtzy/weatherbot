import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone

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
            # executescript() commits implicitly, so rollback has no effect here.
            # The raise below ensures the error is surfaced to the caller.
            conn.rollback()
            raise
    
    conn.close()
    logger.info("Database initialization complete")


SUBSCRIBER_LIMIT = 100


def add_subscriber(chat_id: int, area: str) -> bool | None:
    """Add an area to a subscriber's list.

    Returns:
        True  - area successfully added (new user or new area)
        False - area already in subscriber's list
        None  - subscriber limit reached (chat_id is not yet in DB)
    """
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT areas FROM subscribers WHERE chat_id = ?", (chat_id,)
    ).fetchone()

    if row is None:
        # New user: check global limit first
        count = conn.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
        if count >= SUBSCRIBER_LIMIT:
            conn.close()
            return None
        conn.execute(
            "INSERT INTO subscribers (chat_id, areas) VALUES (?, ?)",
            (chat_id, json.dumps([area])),
        )
        conn.commit()
        conn.close()
        return True

    # Existing user: append area if not already present
    areas = json.loads(row[0])
    if area in areas:
        conn.close()
        return False
    areas.append(area)
    conn.execute(
        "UPDATE subscribers SET areas = ? WHERE chat_id = ?",
        (json.dumps(sorted(areas)), chat_id),
    )
    conn.commit()
    conn.close()
    return True


def remove_subscriber(chat_id: int, area: str) -> bool:
    """Remove an area from a subscriber's list. Deletes the row if no areas remain.

    Returns True if the area was found and removed, False otherwise.
    """
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT areas FROM subscribers WHERE chat_id = ?", (chat_id,)
    ).fetchone()

    if row is None:
        conn.close()
        return False

    areas = json.loads(row[0])
    if area not in areas:
        conn.close()
        return False

    areas.remove(area)
    if not areas:
        conn.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
    else:
        conn.execute(
            "UPDATE subscribers SET areas = ? WHERE chat_id = ?",
            (json.dumps(areas), chat_id),
        )
    conn.commit()
    conn.close()
    return True


def get_subscriptions(chat_id: int) -> list[str]:
    """Return all subscribed area names for a chat."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT areas FROM subscribers WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    conn.close()
    return json.loads(row[0]) if row else []


def get_all_subscribers() -> list[tuple[int, list[str]]]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT chat_id, areas FROM subscribers").fetchall()
    conn.close()
    return [(chat_id, json.loads(areas)) for chat_id, areas in rows]


def update_subscriber_timestamps(chat_id: int, last_sent_at: str, next_scheduled_at: str):
    """Update the last_sent_at and next_scheduled_at timestamps for a subscriber."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE subscribers SET last_sent_at = ?, next_scheduled_at = ? WHERE chat_id = ?",
        (last_sent_at, next_scheduled_at, chat_id),
    )
    conn.commit()
    conn.close()


def get_overdue_subscribers(now_iso: str) -> list[tuple[int, list[str]]]:
    """Get subscribers whose next_scheduled_at is due (<= now)."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT chat_id, areas FROM subscribers WHERE next_scheduled_at IS NULL OR next_scheduled_at <= ?",
        (now_iso,),
    ).fetchall()
    conn.close()
    return [(chat_id, json.loads(areas)) for chat_id, areas in rows]


# ---------------------------------------------------------------------------
# Trivia Database Helpers
# ---------------------------------------------------------------------------

def get_trivia_by_id(trivia_id: int) -> dict | None:
    """Get a trivia item by ID."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT id, text, source_url FROM trivia WHERE id = ?",
        (trivia_id,)
    ).fetchone()
    conn.close()
    if row:
        return {"id": row[0], "text": row[1], "source_url": row[2]}
    return None


def get_trivia_count() -> int:
    """Get the total count of trivia items."""
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM trivia").fetchone()[0]
    conn.close()
    return count


def get_trivia_subscription(chat_id: int) -> dict | None:
    """Get trivia subscription status for a chat."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT trivia_enabled, last_sent_trivia_id FROM trivia_subscriptions WHERE chat_id = ?",
        (chat_id,)
    ).fetchone()
    conn.close()
    if row:
        return {"trivia_enabled": bool(row[0]), "last_sent_trivia_id": row[1]}
    return None


def set_trivia_enabled(chat_id: int, enabled: bool) -> bool:
    """Enable or disable trivia for a chat. Returns True if successful."""
    conn = sqlite3.connect(DB_PATH)
    # Check if subscription exists
    existing = conn.execute(
        "SELECT 1 FROM trivia_subscriptions WHERE chat_id = ?",
        (chat_id,)
    ).fetchone()
    
    if existing:
        conn.execute(
            "UPDATE trivia_subscriptions SET trivia_enabled = ? WHERE chat_id = ?",
            (1 if enabled else 0, chat_id)
        )
    else:
        conn.execute(
            "INSERT INTO trivia_subscriptions (chat_id, trivia_enabled, last_sent_trivia_id) VALUES (?, ?, ?)",
            (chat_id, 1 if enabled else 0, None)
        )
    conn.commit()
    conn.close()
    return True


def update_last_sent_trivia(chat_id: int, trivia_id: int) -> None:
    """Update the last sent trivia ID for a chat."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE trivia_subscriptions SET last_sent_trivia_id = ? WHERE chat_id = ?",
        (trivia_id, chat_id)
    )
    conn.commit()
    conn.close()


def get_trivia_enabled_subscribers() -> list[tuple[int, int | None]]:
    """Get all subscribers with trivia enabled and their last sent trivia ID."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT chat_id, last_sent_trivia_id FROM trivia_subscriptions WHERE trivia_enabled = 1"
    ).fetchall()
    conn.close()
    return [(chat_id, last_id) for chat_id, last_id in rows]


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
        # astimezone handles both offset-aware and naive strings correctly,
        # without clobbering any timezone already embedded in the ISO string.
        start_utc = datetime.fromisoformat(start_str).astimezone(timezone.utc)
        end_utc = datetime.fromisoformat(end_str).astimezone(timezone.utc)
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
        rounded = current_time.replace(minute=0, second=0, microsecond=0)
    
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
    "/trivia on|off - Enable/disable weekly weather trivia (default: off)\n"
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

    if inserted is None:
        await update.message.reply_text("Sorry, the subscriber limit has been reached.")
        return

    if inserted is False:
        await update.message.reply_text(f"You're already subscribed to *{matched_area}*.", parse_mode="Markdown")
        return

    # Fetch current forecast for all subscribed areas (not just the newly added one)
    data = await fetch_forecast()
    all_areas = get_subscriptions(update.effective_chat.id)
    reply = f"Subscribed to *{matched_area}*! You'll receive forecasts every 2 hours."

    now = datetime.now(timezone.utc)
    # Calculate next scheduled time unconditionally - it only depends on now, not the API
    next_scheduled = calculate_next_scheduled_time(now)

    if data:
        valid_period = get_valid_period_text(data)
        forecasts = []
        for area in all_areas:
            forecast = find_area_forecast(data, area)
            if forecast:
                forecasts.append(format_forecast_message(area, forecast, valid_period))
        if forecasts:
            reply += "\n\nCurrent forecast:\n" + "\n\n".join(forecasts)

    await update.message.reply_text(reply, parse_mode="Markdown")

    # Only set timestamps for new subscribers; existing subscribers keep their schedule
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT next_scheduled_at FROM subscribers WHERE chat_id = ?",
        (update.effective_chat.id,)
    ).fetchone()
    conn.close()
    if row and row[0] is None:
        update_subscriber_timestamps(update.effective_chat.id, now.isoformat(), next_scheduled)


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
    remaining = get_subscriptions(update.effective_chat.id)
    reply = f"Unsubscribed from *{matched_area}*."
    if not remaining:
        reply += " You have no more active subscriptions."
    await update.message.reply_text(reply, parse_mode="Markdown")


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


async def cmd_trivia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable or disable weekly trivia. Usage: /trivia on|off"""
    if not context.args or context.args[0].lower() not in ["on", "off"]:
        await update.message.reply_text(
            "Usage: /trivia on - Enable weekly trivia\n"
            "       /trivia off - Disable weekly trivia"
        )
        return
    
    action = context.args[0].lower()
    chat_id = update.effective_chat.id
    
    if action == "on":
        set_trivia_enabled(chat_id, True)
        
        # Get next trivia to send immediately
        subscription = get_trivia_subscription(chat_id)
        last_id = subscription["last_sent_trivia_id"] if subscription else None
        trivia_count = get_trivia_count()
        
        if trivia_count == 0:
            await update.message.reply_text(
                "Weekly trivia enabled. You'll receive trivia every Friday at 10am.\n\n"
                "Note: No trivia available yet."
            )
            return
        
        # Calculate next trivia ID (sequential, wrap around after max)
        next_id = 1 if last_id is None else (last_id % trivia_count) + 1
        trivia = get_trivia_by_id(next_id)
        
        if trivia:
            message = f"Trivia of the week:\n\n{trivia['text']}\n\nSource: {trivia['source_url']}"
            await update.message.reply_text(message, parse_mode="Markdown")
            update_last_sent_trivia(chat_id, next_id)
        else:
            await update.message.reply_text("Weekly trivia enabled. You'll receive trivia every Friday at 10am.")
    else:
        set_trivia_enabled(chat_id, False)
        await update.message.reply_text("Weekly trivia disabled.")


# ---------------------------------------------------------------------------
# Scheduled job: push trivia to enabled subscribers
# ---------------------------------------------------------------------------

async def send_weekly_trivia(app: Application):
    """Send trivia to all subscribers who have trivia enabled."""
    subscribers = get_trivia_enabled_subscribers()
    if not subscribers:
        logger.info("No subscribers with trivia enabled")
        return
    
    trivia_count = get_trivia_count()
    if trivia_count == 0:
        logger.warning("No trivia available to send")
        return
    
    for chat_id, last_id in subscribers:
        # Calculate next trivia ID (sequential, wrap around after max)
        next_id = 1 if last_id is None else (last_id % trivia_count) + 1
        trivia = get_trivia_by_id(next_id)
        
        if trivia:
            message = f"Trivia of the week:\n\n{trivia['text']}\n\nSource: {trivia['source_url']}"
            try:
                await app.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
                update_last_sent_trivia(chat_id, next_id)
                logger.info("Sent trivia id=%d to chat_id=%s", next_id, chat_id)
            except Exception:
                logger.exception("Failed to send trivia to chat_id=%s", chat_id)


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
    
    for chat_id, areas in subscribers:
        messages = []
        for area in areas:
            forecast = find_area_forecast(data, area)
            if forecast:
                messages.append(format_forecast_message(area, forecast, valid_period))

        if not messages:
            continue

        text = "\n\n".join(messages)
        try:
            await app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
            # Update timestamps after successful send
            update_subscriber_timestamps(chat_id, validity_start, next_scheduled)
            logger.info("Sent forecast to chat_id=%s areas=%s, next scheduled: %s",
                        chat_id, areas, next_scheduled)
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
        # Schedule weekly trivia for Friday at 10:00 AM SGT (02:00 UTC)
        scheduler.add_job(
            send_weekly_trivia,
            trigger="cron",
            day_of_week="fri",
            hour=2,  # 02:00 UTC = 10:00 SGT
            minute=0,
            args=[app],
            id="trivia_scheduler",
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
    app.add_handler(CommandHandler("trivia", cmd_trivia))

    logger.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
