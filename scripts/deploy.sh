#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Pulling latest changes..."
git pull

echo "Setting up virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting bot..."
python bot.py
