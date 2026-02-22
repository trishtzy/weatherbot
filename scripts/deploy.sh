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

# Get the version tag being deployed (from main after pull)
# --abbrev=0 ensures we get just the tag name without commit distance suffix
VERSION_TAG=$(git describe --tags --abbrev=0 main 2>/dev/null || echo "")

# Abort deployment if no version tag is found
if [ -z "$VERSION_TAG" ]; then
    echo "Error: No version tag found on main branch. Deployment aborted."
    exit 1
fi

# Get the previous version tag (the one before VERSION_TAG chronologically)
PREV_TAG=$(git tag --sort=-v:refname | grep -A1 "^${VERSION_TAG}$" | tail -1 || echo "")

# Build release notes between previous version and current version
if [ -n "$PREV_TAG" ]; then
    RELEASE_NOTES=$(git log --pretty=format:"• %s" "${PREV_TAG}..${VERSION_TAG}")
else
    # No previous tag found (first release), show all commits in this tag
    RELEASE_NOTES=$(git log --pretty=format:"• %s" "${VERSION_TAG}")
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
