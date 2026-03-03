# Agent Guidelines for Weatherbot

## Build & Development Commands

```bash
# Setup
pip install -r requirements.txt

# Run syntax check (no test framework configured)
python3 -m py_compile bot.py

# Run the bot (requires TELEGRAM_BOT_TOKEN env var)
python bot.py

# Nix development shell
nix develop

# Build Nix package
nix build
```

## Code Style Guidelines

### Imports
- Standard library imports first (json, logging, os, sqlite3, time, datetime)
- Third-party imports second (httpx, apscheduler, dotenv, telegram)
- Group related imports with parentheses for multi-line

### Type Hints
- Use Python 3.10+ union syntax: `str | None`, `bool | None`
- Function signatures must include return types and parameter types
- Example: `def add_subscriber(chat_id: int, area: str) -> bool | None:`

### Naming Conventions
- **Functions/variables**: snake_case (e.g., `get_db_connection`, `uv_index`)
- **Constants**: UPPER_CASE (e.g., `WEATHER_API_URL`, `SUBSCRIBER_LIMIT`)
- **Private globals**: _prefix (e.g., `_forecast_cache`, `_uv_cache_expiry`)
- **Modules**: lowercase (e.g., `bot.py`)

### Formatting
- Two blank lines between top-level functions and classes
- One blank line between methods within a class
- Use double quotes for strings
- Line length: ~100 characters (follow existing patterns)
- Use f-strings for formatting

### Error Handling
- Use `try/except` blocks with specific exceptions
- Log errors with `logger.error()` or `logger.exception()`
- Return `None` for failed operations instead of raising
- Use `resp.raise_for_status()` for HTTP errors

### Async Patterns
- Use `async def` for API calls and I/O operations
- Use `async with httpx.AsyncClient() as client:` pattern
- Call async functions with `await`

### Documentation
- Docstrings for all public functions using triple quotes
- Include "Returns:" section for non-void functions
- Use inline comments sparingly, prefer self-documenting code
- Section headers with `# ---------------------------------------------------------------------------`

### Database
- Use `get_db_connection()` helper for SQLite connections
- Always close connections with `conn.close()`
- Use parameterized queries: `conn.execute("SELECT * FROM t WHERE id = ?", (id,))`
- Foreign keys enabled via `PRAGMA foreign_keys = ON`

### Logging
- Use module-level logger: `logger = logging.getLogger(__name__)`
- Log levels: INFO for operations, ERROR for failures, DEBUG for details
- Format: `logger.info("Message with %s", variable)`

### Caching
- Use global variables with underscore prefix for caches
- Include expiry timestamp with timezone.utc
- Pattern: `_cache`, `_cache_expiry`, `_CACHE_TTL_SECONDS`

### Environment Variables
- Load from .env using `load_dotenv()` at module level
- Required vars: `os.environ["VAR"]` (raises if missing)
- Optional vars: `os.environ.get("VAR", default)`

## Testing

No test framework is currently configured. To add tests:
1. Install pytest: `pip install pytest pytest-asyncio`
2. Create `tests/` directory
3. Run tests: `pytest tests/`
4. Run single test: `pytest tests/test_specific.py::test_function -v`

## Project Structure

```
weatherbot/
├── bot.py              # Main bot application
├── requirements.txt    # Python dependencies
├── flake.nix          # Nix package definition
├── migrations/        # Database migration files (000N_*.sql)
├── scripts/           # Utility scripts (announce_release.py)
└── AGENTS.md         # This file
```

## Database Migrations

- Migration files in `migrations/000N_description.sql` format
- Use PRAGMA user_version to track applied migrations
- Each migration should update user_version: `PRAGMA user_version=N`
- Run automatically on startup via `init_db()`

## Git Conventions

### Commit Guidelines

- **Small and focused**: Each commit should be a single logical change
- **Well-scoped**: Keep changes related to one concern per commit
- **Commit message format**: `<domain>: <action>`
  - Examples: `bot: add UV index fetching`, `db: add subscribers table`, `fix: handle missing API key`
  - Domain describes the area affected (bot, db, api, fix, chore, etc.)
  - Action is a brief imperative description of what changed
- **GPG signing required**: All commits MUST be GPG signed
  - Agent must wait for human to sign commits
  - If human is not available, pause work and do not proceed

### Pull Request Guidelines

- **Title format**: `<prefix>: <brief description>`
  - Prefixes: `fix:`, `feat:`, `chore:`, `refactor:`, `docs:`
  - Examples: `feat: add GET api/v1/collections`, `fix: resolve database connection timeout`
- **Title considerations**: PR titles are used in release notes and changelogs
  - Write for end users and release note readers
  - Be clear about what changed and why it matters
  - Avoid internal technical jargon when possible
  - Example: `feat: add UV index display to weather forecasts` (not `feat: implement fetch_uv_index function`)
