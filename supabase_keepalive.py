#!/usr/bin/env python3
"""Supabase Keepalive — Runs weekly (Monday) via cron to prevent free-tier pausing.
Queries and inserts a keepalive record in each Supabase project.
"""
import requests, json, sys
from datetime import datetime, timezone

SUPABASE_INSTANCES = [
    {
        "name": "TSC_OMROM_E5CC",
        "url": "https://httfohqoikkptywupkrs.supabase.co",
        "key": "sb_publishable_RpXnNg8xARuRnsHLve6aUQ_gMJxc1sf"
    },
    {
        "name": "DB2_qroo",
        "url": "https://qrooubuffimqrsxvpsqk.supabase.co",
        "key": "sb_publishable_jzzpcGGK89Qko-vl7xmyzQ__kSIjyaY"
    }
]

LOG_FILE = "/home/tsc/tsc_app/logs/keepalive.log"

def log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

def keepalive(instance):
    name = instance["name"]
    url = instance["url"]
    key = instance["key"]
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    # 1. Read — query any table to trigger activity
    try:
        r = requests.get(
            f"{url}/rest/v1/loads?limit=1",
            headers=headers, timeout=15
        )
        log(f"  [{name}] READ loads: {r.status_code}")
    except Exception as e:
        log(f"  [{name}] READ failed: {e}")

    # 2. Write — insert a keepalive event (if events table exists)
    try:
        ts = datetime.now(timezone.utc).isoformat()
        r = requests.post(
            f"{url}/rest/v1/events",
            headers=headers, timeout=15,
            json={
                "timestamp": ts,
                "event_type": "KEEPALIVE",
                "furnace": "system",
                "details": f"Weekly keepalive ping — {ts}"
            }
        )
        log(f"  [{name}] WRITE event: {r.status_code}")
    except Exception as e:
        log(f"  [{name}] WRITE failed: {e}")

    # 3. Cleanup — delete old keepalive events (keep last 10)
    try:
        r = requests.get(
            f"{url}/rest/v1/events?event_type=eq.KEEPALIVE&order=id.desc&offset=10&select=id",
            headers=headers, timeout=15
        )
        if r.status_code == 200:
            old_ids = [row["id"] for row in r.json()]
            for oid in old_ids:
                requests.delete(
                    f"{url}/rest/v1/events?id=eq.{oid}",
                    headers=headers, timeout=10
                )
            if old_ids:
                log(f"  [{name}] CLEANUP: deleted {len(old_ids)} old keepalive events")
    except Exception as e:
        log(f"  [{name}] CLEANUP failed: {e}")


if __name__ == "__main__":
    log("=== Supabase Keepalive START ===")
    for inst in SUPABASE_INSTANCES:
        log(f"Processing: {inst['name']} ({inst['url']})")
        keepalive(inst)
    log("=== Supabase Keepalive DONE ===\n")
