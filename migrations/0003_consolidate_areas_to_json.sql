-- Migration 0003: Consolidate areas into JSON array per subscriber
-- Moves from one row per (chat_id, area) to one row per chat_id
-- with areas stored as a JSON array e.g. '["Bedok", "Serangoon"]'

CREATE TABLE subscribers_new (
    chat_id INTEGER PRIMARY KEY,
    areas TEXT NOT NULL DEFAULT '[]',
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sent_at TIMESTAMP,
    next_scheduled_at TIMESTAMP
);

INSERT INTO subscribers_new (chat_id, areas, subscribed_at, last_sent_at, next_scheduled_at)
SELECT
    chat_id,
    json_group_array(area),
    MIN(subscribed_at),
    MAX(last_sent_at),
    MAX(next_scheduled_at)
FROM subscribers
GROUP BY chat_id;

DROP TABLE subscribers;
ALTER TABLE subscribers_new RENAME TO subscribers;

PRAGMA user_version=3;
