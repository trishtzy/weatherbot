-- Migration 0002: Add scheduling columns
-- Adds last_sent_at and next_scheduled_at for time-aligned scheduling

ALTER TABLE subscribers ADD COLUMN last_sent_at TIMESTAMP;
ALTER TABLE subscribers ADD COLUMN next_scheduled_at TIMESTAMP;

PRAGMA user_version=2;
