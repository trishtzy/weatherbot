# SG Weather Bot

A Telegram bot that delivers 2-hourly weather forecasts for Singapore areas, powered by the [data.gov.sg](https://data.gov.sg/) real-time weather API.

## Features

- Subscribe to weather updates for any area in Singapore
- Receive automatic forecasts every 2 hours
- Check the current forecast on demand
- Browse all available forecast areas

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Show help and available commands |
| `/subscribe <area>` | Subscribe to weather updates for an area (e.g. `/subscribe Bedok`) |
| `/unsubscribe` | Stop receiving weather updates |
| `/weather` | Get the current forecast for your subscribed area |
| `/areas` | List all available areas |

## Setup

### Prerequisites

- Python 3.10+
- A [Telegram Bot Token](https://core.telegram.org/bots#creating-a-new-bot) from BotFather
- (Optional) A [data.gov.sg](https://data.gov.sg/) API key

### Install dependencies

```sh
pip install -r requirements.txt
```

### Configure environment variables

Copy the example env file and fill in your values:

```sh
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from Telegram BotFather |
| `DGS_API_KEY` | No | data.gov.sg API key (works without one, but rate limits may apply) |

### Run

```sh
python bot.py
```

### Nix

If you use Nix, a flake is provided:

```sh
nix develop
python bot.py
```

## Data Storage

Subscriber data is stored in a local SQLite database (`subscribers.db`), created automatically on first run.
