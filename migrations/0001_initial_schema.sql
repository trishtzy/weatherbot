-- Migration 0001: Initial schema
-- Creates the subscribers table with composite primary key

CREATE TABLE IF NOT EXISTS subscribers (
    chat_id INTEGER NOT NULL,
    area TEXT NOT NULL,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, area)
);

PRAGMA user_version=1;
