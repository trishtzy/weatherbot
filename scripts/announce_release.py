#!/usr/bin/env python3
"""
Send a release announcement to all subscribers before deploying.

Usage:
    python3 scripts/announce_release.py "v1.2 - Bug fixes and improvements"

The script reads TELEGRAM_BOT_TOKEN from the environment (or .env file),
queries the subscribers database, and sends each unique chat_id a message.
"""

import asyncio
import os
import sqlite3
import sys

import httpx
from dotenv import load_dotenv

# Load .env from project root (one level up from scripts/)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "subscribers.db")
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def get_all_chat_ids() -> list[int]:
    """Return unique chat IDs from the subscribers database."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}, skipping announcement.")
        return []
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT DISTINCT chat_id FROM subscribers").fetchall()
    conn.close()
    return [row[0] for row in rows]


async def send_announcement(chat_id: int, message: str, client: httpx.AsyncClient):
    """Send a message to a single chat_id via the Telegram Bot API."""
    url = TELEGRAM_API_URL.format(token=TELEGRAM_BOT_TOKEN)
    try:
        resp = await client.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }, timeout=10)
        resp.raise_for_status()
        print(f"  Sent to chat_id={chat_id}")
    except Exception as e:
        print(f"  Failed to send to chat_id={chat_id}: {e}")


async def main(version: str, release_notes: str):
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set.")
        sys.exit(1)

    chat_ids = get_all_chat_ids()
    if not chat_ids:
        print("No subscribers found, skipping announcement.")
        return

    message = f"@sgforecastbot has been updated to version *{version}*"
    if release_notes:
        message += f"\n\n*Changes:*\n{release_notes}"

    print(f"Sending release announcement to {len(chat_ids)} subscriber(s)...")
    async with httpx.AsyncClient() as client:
        tasks = [send_announcement(chat_id, message, client) for chat_id in chat_ids]
        await asyncio.gather(*tasks)
    print("Announcement sent.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: announce_release.py <version> <release-notes>")
        sys.exit(1)

    version = sys.argv[1]
    release_notes = sys.argv[2] if len(sys.argv) > 2 else ""
    asyncio.run(main(version, release_notes))
