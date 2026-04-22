#!/usr/bin/env python3
"""
sync_check.py — Daily reconciliation SQLite ↔ Supabase
Run via cron at 03:00: 0 3 * * * cd /home/tsc/tsc_app && python3 sync_check.py >> logs/sync.log 2>&1

Checks row counts, detects gaps, triggers backfill if needed,
and sends a summary to Telegram.
"""
import sqlite3, os, sys, requests, json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tsc.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TSC_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7024795874")

TABLES = ["readings", "loads", "events", "temperature_tracking", "alarms"]


def supa_headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def supa_count(table):
    try:
        r = requests.head(f"{SUPABASE_URL}/rest/v1/{table}?select=*",
                           headers={**supa_headers(), "Prefer": "count=exact"}, timeout=15)
        return int(r.headers.get("Content-Range", "").split("/")[1])
    except:
        return -1


def sqlite_count(table):
    try:
        conn = sqlite3.connect(DB_FILE)
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.close()
        return count
    except:
        return -1


def send_telegram(msg):
    if not TELEGRAM_TOKEN:
        print(f"[TG] No token, skipping: {msg[:80]}")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        print(f"[TG] Error: {e}")


def main():
    now = datetime.now().isoformat()
    print(f"\n{'='*50}")
    print(f"SYNC CHECK — {now}")
    print(f"{'='*50}")

    results = []
    needs_backfill = False

    for table in TABLES:
        local = sqlite_count(table)
        remote = supa_count(table)
        diff = local - remote if remote >= 0 else local
        pct = round(diff / max(local, 1) * 100, 1)

        if remote < 0:
            status = "❌ MISSING"
            needs_backfill = True
        elif diff > 0 and pct > 1:
            status = f"⚠️ -{diff}"
            needs_backfill = True
        elif diff < 0:
            status = f"📌 Supa+{abs(diff)}"
        else:
            status = "✅"

        results.append((table, local, remote, diff, status))
        print(f"  {table}: SQLite={local} | Supabase={remote} | {status}")

    # Build report
    lines = ["📊 *TSC Sync Check*\n"]
    for table, local, remote, diff, status in results:
        lines.append(f"  {status} `{table}`: {local} / {remote}")

    if needs_backfill:
        lines.append("\n⚠️ Gap detectado — ejecutando backfill...")
        print("\nTriggering backfill...")
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "backfill_supabase.py")],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            lines.append("✅ Backfill completado")
            # Re-check counts
            for table in TABLES:
                new_remote = supa_count(table)
                local = sqlite_count(table)
                lines.append(f"  `{table}`: {local} / {new_remote}")
        else:
            lines.append(f"❌ Backfill failed: {result.stderr[:200]}")
        print(result.stdout[-500:] if result.stdout else "")
    else:
        lines.append("\n✅ Todo sincronizado")

    msg = "\n".join(lines)
    print(f"\nTelegram report:\n{msg}")
    send_telegram(msg)


if __name__ == "__main__":
    main()
