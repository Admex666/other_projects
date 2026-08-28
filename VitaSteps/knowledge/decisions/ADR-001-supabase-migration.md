---
id: ADR-001
type: decision
name: ADR-001 Migration from Google Sheets to Supabase
status: accepted
date: 2026-07-21
replaces: null
related:
  - "[[supabase]]"
  - "[[customer]]"
  - "[[run]]"
---

# Decision: Migration from Google Sheets to Supabase

## Context
In early versions, Google Sheets (via Google Sheets API service accounts) served as the database for registrations, Tally webhooks, and Foxpost tracking. As order volume grew, Sheets caused rate limits, race conditions during simultaneous checkouts, and severe data inconsistency risks.

## Decision
Migrate 100% of data persistence to Supabase (PostgreSQL). Split the data model into normalized tables: `runners`, `orders`, `runs`, `shipments`.

## Consequences
* Immediate transactional consistency and atomicity.
* Enables robust Row-Level Security (RLS) and real-time frontend subscriptions.
* All previous Sheets entries were migrated cleanly via `migrate_sheets_data.js`.
