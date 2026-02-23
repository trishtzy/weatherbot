-- Migration 0005: Create trivia_subscriptions table
-- Tracks which subscribers have trivia enabled and their progress

CREATE TABLE trivia_subscriptions (
    chat_id INTEGER PRIMARY KEY,
    trivia_enabled INTEGER NOT NULL DEFAULT 0 CHECK (trivia_enabled IN (0, 1)),
    last_sent_trivia_id INTEGER,
    FOREIGN KEY (chat_id) REFERENCES subscribers(chat_id) ON DELETE CASCADE
);

PRAGMA user_version=5;
