-- Migration 0004: Create trivia table
-- Stores 365 unique weather forecasting facts

CREATE TABLE trivia (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    source_url TEXT NOT NULL
);

PRAGMA user_version=4;
