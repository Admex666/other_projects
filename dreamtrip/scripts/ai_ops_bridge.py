# -*- coding: utf-8 -*-
r"""
AI Ops Bridge for Dreamtrip (Optivoya)
Connects Dreamtrip's local work items and decisions with the central AI Ops Hub (E:\Data\AI_ops).
"""

import os
import sys
import glob
import re
import argparse

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

AI_OPS_CORE = r"E:\Data\AI_ops\core"
if os.path.exists(AI_OPS_CORE):
    sys.path.insert(0, AI_OPS_CORE)
    try:
        import tracker
        import db
    except ImportError:
        tracker = None
        db = None
else:
    tracker = None
    db = None

PROJECT_ID = "Dreamtrip"
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_db():
    if db:
        return db.get_connection()
    import sqlite3
    db_path = r"E:\Data\AI_ops\store\ai_ops.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def sync_work_items():
    """Scans work/active/ and syncs tasks to central AI Ops Hub."""
    active_dir = os.path.join(WORKSPACE_ROOT, "work", "active")
    if not os.path.exists(active_dir):
        print(f"[AI_OPS BRIDGE] No work/active directory found at {active_dir}")
        return

    work_files = glob.glob(os.path.join(active_dir, "*.md"))
    conn = get_db()
    c = conn.cursor()

    synced_count = 0
    for wf in work_files:
        filename = os.path.basename(wf)
        try:
            with open(wf, "r", encoding="utf-8") as f:
                content = f.read()

            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else filename

            owner_match = re.search(r"owner:\s*([a-zA-Z0-9_\-]+)", content)
            owner = owner_match.group(1).strip() if owner_match else "fullstack_engineer"

            status_match = re.search(r"status:\s*([a-zA-Z0-9_\-]+)", content)
            raw_status = status_match.group(1).strip() if status_match else "pending"
            status = "in_progress" if raw_status in ["active", "in_progress"] else ("completed" if raw_status == "completed" else "pending")

            priority_match = re.search(r"priority:\s*([a-zA-Z0-9_\-]+)", content)
            priority = priority_match.group(1).strip() if priority_match else "high"

            # Check if exists
            c.execute("SELECT id FROM tasks WHERE project_id = ? AND title = ?", (PROJECT_ID, title))
            existing = c.fetchone()
            if existing:
                c.execute("UPDATE tasks SET assigned_agent = ?, status = ?, priority = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                          (owner, status, priority, existing[0]))
            else:
                c.execute("""INSERT INTO tasks (project_id, title, description, assigned_agent, status, priority, created_at, updated_at)
                             VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                          (PROJECT_ID, title, f"Synced from {filename}", owner, status, priority))
            synced_count += 1
        except Exception as e:
            print(f"[AI_OPS BRIDGE] Error parsing {filename}: {e}")

    conn.commit()
    conn.close()
    print(f"[AI_OPS BRIDGE] Successfully synced {synced_count} work items to central AI Ops Hub!")

def log_task(title, agent="fullstack_engineer", priority="medium", desc=None):
    if tracker:
        tid = tracker.log_task(PROJECT_ID, title, desc, agent, priority)
        print(f"[AI_OPS BRIDGE] Task created with ID: {tid} assigned to {agent}")
    else:
        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT INTO tasks (project_id, title, description, assigned_agent, status, priority, created_at, updated_at)
                     VALUES (?, ?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                  (PROJECT_ID, title, desc, agent, priority))
        tid = c.lastrowid
        conn.commit()
        conn.close()
        print(f"[AI_OPS BRIDGE] Task created with ID: {tid} assigned to {agent}")

def add_memory(category, key, value, tags=None):
    if tracker:
        mid = tracker.add_memory(PROJECT_ID, category, key, value, tags)
        print(f"[AI_OPS BRIDGE] Memory saved with ID: {mid} [{category}] {key}")
    else:
        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT INTO memories (project_id, category, key, value, tags, created_at, updated_at)
                     VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                     ON CONFLICT(project_id, category, key) DO UPDATE SET
                        value = excluded.value, tags = excluded.tags, updated_at = CURRENT_TIMESTAMP""",
                  (PROJECT_ID, category, key, value, tags))
        mid = c.lastrowid
        conn.commit()
        conn.close()
        print(f"[AI_OPS BRIDGE] Memory saved with ID: {mid} [{category}] {key}")

def show_status():
    conn = get_db()
    c = conn.cursor()
    print(f"==================================================")
    print(f"   AI OPS MISSION CONTROL — DREAMTRIP STATUS")
    print(f"==================================================")
    print("Registered Agents:")
    for a in c.execute("SELECT id, name, status FROM agents").fetchall():
        print(f" - [{a['status'].upper()}] {a['name']} ({a['id']})")
    print("\nDreamtrip Active / Pending Tasks:")
    for t in c.execute("SELECT id, title, assigned_agent, status, priority FROM tasks WHERE project_id = ?", (PROJECT_ID,)).fetchall():
        print(f" #{t['id']} [{t['status']}] {t['title']} -> {t['assigned_agent']} (prio: {t['priority']})")
    print("\nDreamtrip Persistent Memories:")
    for m in c.execute("SELECT category, key, value FROM memories WHERE project_id = ?", (PROJECT_ID,)).fetchall():
        print(f" • [{m['category']}] {m['key']}: {m['value'][:80]}...")
    conn.close()
    print(f"==================================================")

def main():
    parser = argparse.ArgumentParser(description="Dreamtrip AI Ops Bridge")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("sync", help="Sync active work items to AI Ops Hub")
    sub.add_parser("status", help="Display Mission Control status for Dreamtrip")

    t_parser = sub.add_parser("log-task", help="Log a task")
    t_parser.add_argument("--title", required=True)
    t_parser.add_argument("--agent", default="fullstack_engineer")
    t_parser.add_argument("--priority", default="medium")
    t_parser.add_argument("--desc")

    m_parser = sub.add_parser("add-memory", help="Add persistent memory / decision")
    m_parser.add_argument("--category", required=True, choices=["learning", "decision", "standard", "domain"])
    m_parser.add_argument("--key", required=True)
    m_parser.add_argument("--value", required=True)
    m_parser.add_argument("--tags")

    args = parser.parse_args()

    if args.cmd == "sync":
        sync_work_items()
    elif args.cmd == "status":
        show_status()
    elif args.cmd == "log-task":
        log_task(args.title, args.agent, args.priority, args.desc)
    elif args.cmd == "add-memory":
        add_memory(args.category, args.key, args.value, args.tags)
    else:
        show_status()

if __name__ == "__main__":
    main()
