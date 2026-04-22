#!/usr/bin/env python3
"""
backfill_supabase.py — One-time script to sync SQLite → Supabase
Finds rows in SQLite missing from Supabase and inserts them in batches.
"""
import sqlite3, os, sys, json, time, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tsc.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
BATCH_SIZE = 50


def headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json", "Prefer": "return=minimal"}


def supa_count(table):
    try:
        r = requests.head(f"{SUPABASE_URL}/rest/v1/{table}?select=*",
                           headers={**headers(), "Prefer": "count=exact"}, timeout=15)
        cr = r.headers.get("Content-Range", "")
        return int(cr.split("/")[1])
    except:
        return -1


def supa_get_timestamps(table):
    """Get all timestamps from Supabase for dedup."""
    ts_set = set()
    offset = 0
    while True:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table}?select=timestamp&order=timestamp.asc&offset={offset}&limit=1000",
            headers=headers(), timeout=30)
        if r.status_code != 200 or not r.json():
            break
        for row in r.json():
            ts_set.add(row["timestamp"])
        if len(r.json()) < 1000:
            break
        offset += 1000
    return ts_set


def supa_batch_insert(table, rows):
    if not rows:
        return 0
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}",
                       headers=headers(), json=rows, timeout=30)
    if r.status_code in (200, 201):
        return len(rows)
    else:
        print(f"  ❌ {table} batch insert failed {r.status_code}: {r.text[:300]}")
        return 0


def backfill_table(table, columns, transform=None):
    print(f"\n{'='*50}")
    print(f"BACKFILLING: {table}")
    print(f"{'='*50}")

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    has_ts = "timestamp" in columns
    order = "timestamp ASC" if has_ts else "id ASC"
    local_rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall()
    conn.close()

    local_count = len(local_rows)
    supa_ct = supa_count(table)
    print(f"  SQLite: {local_count} rows | Supabase: {supa_ct} rows")

    if supa_ct < 0:
        print(f"  ⚠️ Table {table} might not exist in Supabase — will try inserting anyway")
        supa_ct = 0

    if local_count <= supa_ct:
        print(f"  ✅ Already in sync (or Supabase has more)!")
        return 0

    # Dedup by timestamp
    existing_ts = set()
    if has_ts and supa_ct > 0:
        print(f"  Fetching Supabase timestamps for dedup...")
        existing_ts = supa_get_timestamps(table)
        print(f"  Got {len(existing_ts)} existing timestamps")

    # Find missing
    missing = []
    for row in local_rows:
        d = dict(row)
        if has_ts and d.get("timestamp") in existing_ts:
            continue
        supa_row = {}
        for col in columns:
            if col == "id":
                continue
            val = d.get(col)
            if val is None and col in ("temp_sales", "temp_cameras", "temperature", "set_point"):
                val = 0
            supa_row[col] = val
        if transform:
            supa_row = transform(supa_row, d)
        missing.append(supa_row)

    print(f"  Missing in Supabase: {len(missing)} rows")
    if not missing:
        return 0

    inserted = 0
    for i in range(0, len(missing), BATCH_SIZE):
        batch = missing[i:i + BATCH_SIZE]
        n = supa_batch_insert(table, batch)
        inserted += n
        pct = round((i + len(batch)) / len(missing) * 100)
        print(f"  Batch {i // BATCH_SIZE + 1}: +{n} rows ({pct}%)")
        time.sleep(0.3)

    print(f"  ✅ Backfilled {inserted}/{len(missing)} rows")
    return inserted


def main():
    print("=" * 60)
    print("TSC SUPABASE BACKFILL — SQLite → Supabase")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ SUPABASE_URL or SUPABASE_ANON_KEY not set")
        sys.exit(1)

    total = 0

    # readings
    total += backfill_table("readings",
        ["id", "timestamp", "furnace", "temp_sales", "temp_cameras", "set_point"])

    # loads
    def xform_load(supa_row, local_row):
        name = local_row.get("name", "")
        furnace = local_row.get("furnace", "")
        if furnace and f"[{furnace}]" not in name:
            supa_row["name"] = f"{name} [{furnace}]"
        return supa_row

    total += backfill_table("loads",
        ["id", "name", "date", "start_time", "end_time", "status", "ot_number",
         "duration_min", "weight", "furnace", "duration_s", "total_minutes"],
        transform=xform_load)

    # events
    total += backfill_table("events",
        ["id", "timestamp", "event_type", "furnace", "details", "email_sent", "whatsapp_sent"])

    # temperature_tracking
    total += backfill_table("temperature_tracking",
        ["id", "timestamp", "furnace", "temperature", "ot_number",
         "subload_summary", "load_status", "date"])

    # alarms
    total += backfill_table("alarms",
        ["id", "timestamp", "alarm_type", "furnace", "details", "resolved",
         "resolved_time", "date"])

    print(f"\n{'='*60}")
    print(f"BACKFILL COMPLETE — Total inserted: {total}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
