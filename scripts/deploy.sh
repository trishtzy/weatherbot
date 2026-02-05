#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Pulling latest changes..."
git pull

echo "Setting up virtual environment..."
python3 -m venv .venv

echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

echo "Stopping existing bot if running..."
pkill -f "\.venv/bin/python bot\.py" || true

echo "Starting bot in background..."
nohup .venv/bin/python bot.py >> bot.log 2>&1 &
echo "Bot started (PID: $!) — logs: bot.log"
