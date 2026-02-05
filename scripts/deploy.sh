#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Pulling latest changes..."
git pull

echo "Setting up virtual environment..."
python3 -m venv .venv

echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

echo "Starting bot..."
.venv/bin/python bot.py
