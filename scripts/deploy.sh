#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Pulling latest changes..."
PREV_HEAD=$(git rev-parse HEAD)
git pull
NEW_HEAD=$(git rev-parse HEAD)

echo "Setting up virtual environment..."
python3 -m venv .venv

echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

# Build release notes from commits between previous and new HEAD
if [ "$PREV_HEAD" != "$NEW_HEAD" ]; then
    RELEASE_NOTES=$(git log --pretty=format:"• %s" "${PREV_HEAD}..${NEW_HEAD}")
else
    RELEASE_NOTES=""
fi

# Get the version tag being deployed (from main after pull)
VERSION_TAG=$(git describe --tags main 2>/dev/null || echo "")

# Abort deployment if no version tag is found
if [ -z "$VERSION_TAG" ]; then
    echo "Error: No version tag found on main branch. Deployment aborted."
    exit 1
fi

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

# Wait a moment for the bot to fully initialize
sleep 2

# Send post-deployment announcement to all subscribers
echo "Sending deployment completion notification to subscribers..."
.venv/bin/python3 scripts/announce_release.py "$VERSION_TAG" "$RELEASE_NOTES" || true
