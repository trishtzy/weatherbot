import argparse
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone

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

def init_db():
    conn = sqlite3.connect(DB_PATH)
    # Migrate from old single-area schema if needed
    cursor = conn.execute("PRAGMA table_info(subscribers)")
    columns = {row[1]: row[5] for row in cursor.fetchall()}  # name -> pk flag
    if columns and columns.get("chat_id") and not columns.get("area", 0):
        # Old schema: chat_id is sole PK. Recreate with composite key.
        conn.executescript(
            """
            ALTER TABLE subscribers RENAME TO _subscribers_old;
            CREATE TABLE subscribers (
                chat_id INTEGER NOT NULL,
                area TEXT NOT NULL,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, area)
            );
            INSERT OR IGNORE INTO subscribers (chat_id, area, subscribed_at)
                SELECT chat_id, area, subscribed_at FROM _subscribers_old;
            DROP TABLE _subscribers_old;
            """
        )
    else:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS subscribers (
                chat_id INTEGER NOT NULL,
                area TEXT NOT NULL,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, area)
            )
            """
        )
    conn.commit()
    conn.close()


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


# ---------------------------------------------------------------------------
# Weather API
# ---------------------------------------------------------------------------

async def fetch_forecast() -> dict | None:
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
    return data.get("data")


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

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm the SG Weather Bot.\n\n"
        "Commands:\n"
        "/subscribe <area> - Get 2-hourly weather updates (multiple areas OK)\n"
        "/unsubscribe <area> - Stop updates for an area\n"
        "/weather - Current forecast for your subscribed areas\n"
        "/areas - List all available areas\n\n"
        "Example: /subscribe Bedok"
    )


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
    if data:
        forecast = find_area_forecast(data, matched_area)
        valid_period = get_valid_period_text(data)
        if forecast:
            reply += "\n\nCurrent forecast:\n" + format_forecast_message(matched_area, forecast, valid_period)

    await update.message.reply_text(reply, parse_mode="Markdown")


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

async def send_scheduled_updates(app: Application):
    subscribers = get_all_subscribers()
    if not subscribers:
        return

    data = await fetch_forecast()
    if data is None:
        logger.warning("Scheduled update: could not fetch forecast")
        return

    valid_period = get_valid_period_text(data)

    for chat_id, area in subscribers:
        forecast = find_area_forecast(data, area)
        if forecast is None:
            continue
        text = format_forecast_message(area, forecast, valid_period)
        try:
            await app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception:
            logger.exception("Failed to send update to chat_id=%s", chat_id)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def make_post_init(interval_minutes: int):
    async def post_init(app: Application):
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            send_scheduled_updates,
            trigger="interval",
            minutes=interval_minutes,
            args=[app],
        )
        scheduler.start()
    return post_init


def main():
    parser = argparse.ArgumentParser(description="SG Weather Telegram Bot")
    parser.add_argument(
        "--interval",
        type=int,
        default=120,
        metavar="MINUTES",
        help="forecast update interval in minutes (default: 120)",
    )
    args = parser.parse_args()

    init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(make_post_init(args.interval)).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("areas", cmd_areas))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    app.add_handler(CommandHandler("weather", cmd_weather))

    logger.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
