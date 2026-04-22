#!/usr/bin/env python3
"""
TSC — Cleanup script for test data.
Run this ONCE before going live on Monday 23 March 2026.
It will:
  1. Delete all rows from loads, events, readings, work_orders in SQLite
  2. Delete all rows from loads, events in Supabase
  3. Reset auto-increment counters
  4. Keep the schema intact

Usage:
  cd ~/furnace_monitor
  source .venv/bin/activate
  python3 cleanup_test_data.py          # dry-run (shows what would be deleted)
  python3 cleanup_test_data.py --confirm   # actually deletes
"""
import sys
import os
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tsc.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

DRY_RUN = "--confirm" not in sys.argv

def main():
    if DRY_RUN:
        print("=" * 60)
        print("  DRY RUN — no data will be deleted")
        print("  Run with --confirm to actually delete")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  ⚠️  LIVE RUN — DATA WILL BE DELETED")
        print("=" * 60)
        answer = input("Are you sure? Type 'YES' to confirm: ")
        if answer != "YES":
            print("Aborted.")
            return

    # ─── SQLite ──────────────────────────────────────────────
    print("\n--- SQLite ---")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    tables = ["readings", "events", "work_orders", "loads"]
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} rows", end="")
        if not DRY_RUN and count > 0:
            conn.execute(f"DELETE FROM {table}")
            conn.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
            print(" → DELETED ✅")
        else:
            print(" → would be deleted" if count > 0 else " → empty")

    if not DRY_RUN:
        conn.execute("VACUUM")
        conn.commit()
        print("  SQLite VACUUMed ✅")
    conn.close()

    # ─── Supabase ────────────────────────────────────────────
    print("\n--- Supabase ---")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("  ⚠️  Supabase not configured (missing SUPABASE_URL or SUPABASE_ANON_KEY)")
        return

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    supa_tables = ["events", "loads"]
    for table in supa_tables:
        try:
            r = requests.get(
                f"{SUPABASE_URL}/rest/v1/{table}?select=id",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
                timeout=10
            )
            count = len(r.json()) if r.status_code == 200 else "?"
            print(f"  {table}: {count} rows", end="")

            if not DRY_RUN:
                # Delete all rows (PostgREST requires a filter, use id > 0)
                r2 = requests.delete(
                    f"{SUPABASE_URL}/rest/v1/{table}?id=gt.0",
                    headers=headers,
                    timeout=10
                )
                if r2.status_code in (200, 204):
                    print(" → DELETED ✅")
                else:
                    print(f" → ERROR {r2.status_code}: {r2.text[:100]}")
            else:
                print(" → would be deleted" if count and count != "?" and count > 0 else "")
        except Exception as e:
            print(f"  {table}: ERROR - {e}")

    print("\n" + "=" * 60)
    if DRY_RUN:
        print("Dry run complete. Run with --confirm to actually delete.")
    else:
        print("✅ All test data deleted. Ready for production on Monday!")
    print("=" * 60)


if __name__ == "__main__":
    main()
