-- Migration 0003: Migrate from old single-area schema
-- Old schema had chat_id as sole primary key, new schema has composite (chat_id, area)
-- This migration handles the transition safely

-- Only run if old schema detected (single primary key on chat_id)
-- Check if we need to migrate by looking at table structure
-- SQLite doesn't support IF statements, so we'll handle this in Python code

-- For now, this is a placeholder - the actual migration logic is in Python
-- We keep it simple: if the table exists with old structure, it will be
-- handled by the application's init_db logic before migrations run

PRAGMA user_version=3;
