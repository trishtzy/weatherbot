#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Pulling latest changes..."
git pull

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting bot..."
python bot.py
