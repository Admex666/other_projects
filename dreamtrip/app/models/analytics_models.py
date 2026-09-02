"""
Optivoya Analytics & User Storage Models
SQLite-backed, fully Postgres / Supabase compatible data layer.
"""
import os
import json
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime

def get_db_path():
    # Vercel serverless environment has read-only root filesystem except /tmp
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return "/tmp/analytics.db"
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "analytics.db")

def get_db_connection():
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_analytics_db():
    """Initializes tables matching Supabase / PostgreSQL schema."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table (Beta Users & Advisors)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS beta_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        company_name TEXT,
        email TEXT,
        role TEXT DEFAULT 'advisor',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active_at TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        notes TEXT
    )
    """)

    # 2. User Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_event_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        device_info TEXT,
        ip_address TEXT,
        searches_count INTEGER DEFAULT 0
    )
    """)

    # 3. Telemetry & Analytics Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telemetry_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT UNIQUE,
        session_id TEXT,
        user_id TEXT NOT NULL,
        event_type TEXT NOT NULL, -- search_started, search_completed, item_selected, proposal_exported, error
        module TEXT NOT NULL,     -- destination_matcher, flight_intelligence, accommodation_intelligence, master_planner, proposal
        search_params TEXT,       -- JSON formatted search inputs
        duration_ms REAL,
        results_count INTEGER,
        success INTEGER DEFAULT 1,
        error_message TEXT,
        meta_data TEXT,           -- Extra JSON telemetry
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Default starter users if not present
    cursor.execute("SELECT COUNT(*) FROM beta_users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO beta_users (username, password_hash, full_name, company_name, email, role, is_active)
        VALUES 
        ('admin', 'optivoya2024', 'Adminisztrátor', 'Optivoya HQ', 'admin@optivoya.com', 'admin', 1),
        ('bean', 'bean', 'Bean (Founder)', 'Optivoya HQ', 'adam@optivoya.com', 'advisor', 1)
        """)


    conn.commit()
    conn.close()

# Auto-initialize database on module import
init_analytics_db()
