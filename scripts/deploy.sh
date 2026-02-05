#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Pulling latest changes..."
git pull

echo "Setting up virtual environment..."
python3 -m venv .venv

echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

echo "Installing systemd service..."
cp scripts/weatherbot.service /etc/systemd/system/weatherbot.service
systemctl daemon-reload
systemctl enable weatherbot

echo "Stopping any running bot processes..."
systemctl stop weatherbot || true
pkill -f "python.*bot\.py" || true

echo "Starting bot..."
systemctl start weatherbot
echo "Bot is running — check status with: systemctl status weatherbot"
