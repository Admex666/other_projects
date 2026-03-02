-- Migration 00009: Bővítjük a game_status enumot a 'trump_selection' és 'announce' értékekkel

ALTER TYPE game_status ADD VALUE IF NOT EXISTS 'trump_selection' AFTER 'bidding';
ALTER TYPE game_status ADD VALUE IF NOT EXISTS 'announce' AFTER 'trump_selection';
