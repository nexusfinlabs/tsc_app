"""
TSC Furnace Monitor — Database Layer (Dual-Write)
SQLite (always, instant) + Supabase PostgreSQL (async, best-effort via REST API).

If Supabase is unreachable, data is ALWAYS safe in SQLite local.
"""
import sqlite3
import os
import threading
import json
from datetime import datetime, timezone

import requests

# ─── CONFIG ──────────────────────────────────────────────────────────────────

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tsc.db")

# Supabase REST API (works over HTTPS — no IPv6 issues)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_KEY)

if SUPABASE_ENABLED:
    print(f"[DB] Supabase dual-write ENABLED → {SUPABASE_URL}")
else:
    print("[DB] Supabase dual-write DISABLED (missing SUPABASE_URL or SUPABASE_ANON_KEY)")

# ─── TEMP TRACKER STATE ──────────────────────────────────────────────────────

temp_tracker = {
    "enabled": True,   # Always ON by default — survives restarts
    "interval_s": 30,  # default 30s
}
temp_tracker_lock = threading.Lock()

def get_temp_tracker_state():
    with temp_tracker_lock:
        return dict(temp_tracker)

def set_temp_tracker(enabled=None, interval_s=None):
    with temp_tracker_lock:
        if enabled is not None:
            temp_tracker["enabled"] = bool(enabled)
        if interval_s is not None:
            temp_tracker["interval_s"] = max(30, min(300, int(interval_s)))
    state = get_temp_tracker_state()
    print(f"[TRACKER] {'ON' if state['enabled'] else 'OFF'} — interval {state['interval_s']}s")
    return state


# ─── SQLITE ──────────────────────────────────────────────────────────────────

try:
    from zoneinfo import ZoneInfo
    MADRID_TZ = ZoneInfo("Europe/Madrid")
except ImportError:
    # Python < 3.9 fallback: CEST = UTC+2 (summer), CET = UTC+1 (winter)
    MADRID_TZ = timezone(timedelta(hours=2))


def get_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _now():
    return datetime.now(MADRID_TZ).isoformat()


def _today():
    return datetime.now(MADRID_TZ).strftime("%Y-%m-%d")


def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        furnace TEXT NOT NULL,
        slave_id INTEGER,
        temp_sales REAL,
        temp_cameras REAL,
        set_point REAL,
        raw_value INTEGER,
        status TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS loads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        furnace TEXT NOT NULL,
        date TEXT NOT NULL,
        start_time TEXT,
        end_time TEXT,
        duration_s INTEGER,
        total_minutes REAL,
        client_id TEXT,
        pieces_id TEXT,
        status TEXT
    )""")

    # Migration: add new columns if they don't exist (for existing databases)
    for col, col_type in [("total_minutes", "REAL"), ("client_id", "TEXT"), ("pieces_id", "TEXT"),
                           ("ot_number", "TEXT"), ("duration_min", "INTEGER"),
                           ("real_start_time", "TEXT"), ("check_set_point", "REAL"),
                           ("temp_start", "REAL"), ("temp_finish", "REAL")]:
        try:
            conn.execute(f"ALTER TABLE loads ADD COLUMN {col} {col_type}")
            print(f"[DB] ✅ Added column loads.{col}")
        except Exception:
            pass  # Column already exists

    conn.execute("""CREATE TABLE IF NOT EXISTS work_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        load_id INTEGER REFERENCES loads(id),
        ot_number TEXT NOT NULL,
        client_id TEXT,
        client_name TEXT,
        piece_id TEXT,
        piece_ref TEXT,
        extra_id_1 TEXT,
        extra_id_2 TEXT,
        extra_id_3 TEXT,
        required_min REAL NOT NULL DEFAULT 30,
        start_time TEXT,
        end_time TEXT,
        status TEXT,
        process TEXT,
        weight TEXT,
        reference TEXT,
        done INTEGER DEFAULT 0,
        done_time TEXT,
        duration_min REAL,
        piece_type TEXT,
        material TEXT,
        industry TEXT,
        target_temp REAL,
        hold_time_min INTEGER,
        cooling_method TEXT,
        quality_check TEXT DEFAULT 'pending',
        quality_notes TEXT,
        batch_id TEXT
    )""")

    # Migration: work_orders sub-load columns (for existing databases)
    for col, col_type in [("weight", "TEXT"), ("reference", "TEXT"), ("done", "INTEGER DEFAULT 0"),
                           ("done_time", "TEXT"), ("duration_min", "REAL"),
                           ("piece_type", "TEXT"), ("material", "TEXT"), ("industry", "TEXT"),
                           ("target_temp", "REAL"), ("hold_time_min", "INTEGER"),
                           ("cooling_method", "TEXT"), ("quality_check", "TEXT DEFAULT 'pending'"),
                           ("quality_notes", "TEXT"), ("batch_id", "TEXT")]:
        try:
            conn.execute(f"ALTER TABLE work_orders ADD COLUMN {col} {col_type}")
            print(f"[DB] ✅ Added column work_orders.{col}")
        except Exception:
            pass

    conn.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        event_type TEXT NOT NULL,
        furnace TEXT,
        details TEXT,
        email_sent INTEGER DEFAULT 0,
        whatsapp_sent INTEGER DEFAULT 0
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS temperature_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        furnace TEXT NOT NULL,
        temperature REAL,
        ot_number TEXT,
        subload_summary TEXT,
        load_status TEXT,
        date TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS llm_searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        question TEXT NOT NULL,
        sql_generated TEXT,
        engine TEXT,
        result_count INTEGER DEFAULT 0,
        error TEXT,
        date TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS alarms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        alarm_type TEXT NOT NULL,
        furnace TEXT,
        details TEXT,
        resolved INTEGER DEFAULT 0,
        resolved_time TEXT,
        date TEXT
    )""")
    # Migration: add weight column to loads if missing
    for col, col_type in [("weight", "TEXT")]:
        try:
            conn.execute(f"ALTER TABLE loads ADD COLUMN {col} {col_type}")
            print(f"[DB] ✅ Added column loads.{col}")
        except Exception:
            pass
    conn.execute("CREATE INDEX IF NOT EXISTS idx_readings_ts ON readings(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_readings_furnace ON readings(furnace)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_loads_date ON loads(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_alarms_ts ON alarms(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_temp_tracking_date ON temperature_tracking(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_llm_searches_date ON llm_searches(date)")
    conn.execute("""CREATE TABLE IF NOT EXISTS alarm_thresholds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL UNIQUE,
        threshold REAL NOT NULL,
        updated_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS alarm_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        threshold REAL NOT NULL,
        temperature REAL NOT NULL,
        triggered_at TEXT DEFAULT (datetime('now')),
        silenced_at TEXT,
        resolved_at TEXT,
        status TEXT DEFAULT 'active'
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_alarm_events_triggered ON alarm_events(triggered_at)")
    conn.commit()
    conn.close()
    print(f"[DB] SQLite initialized: {DB_FILE}")


def save_llm_search(question, sql_generated=None, engine=None, result_count=0, error=None):
    """Save an LLM search to SQLite + Supabase."""
    ts = _now()
    today = _today()
    conn = get_db()
    conn.execute(
        "INSERT INTO llm_searches (timestamp, question, sql_generated, engine, result_count, error, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ts, question, sql_generated, engine, result_count, error, today)
    )
    conn.commit()
    conn.close()

    # Supabase async
    _supa_async(_supa_insert, "llm_searches", {
        "timestamp": ts,
        "question": question,
        "sql_generated": sql_generated or "",
        "engine": engine or "",
        "result_count": result_count,
        "error": error or "",
        "date": today
    })


# ─── SUPABASE REST API ───────────────────────────────────────────────────────

def _supa_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }


def _supa_insert(table, data):
    """Insert a row into Supabase via REST API (async, best-effort)."""
    if not SUPABASE_ENABLED:
        return
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=_supa_headers(),
            json=data,
            timeout=10
        )
        if r.status_code in (200, 201):
            print(f"[SUPA] ✅ {table} INSERT OK")
        else:
            print(f"[SUPA] ⚠️ {table} INSERT {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[SUPA] ❌ {table} INSERT FAILED: {e}")


def _supa_update(table, match_col, match_val, data):
    """Update rows in Supabase via REST API (async, best-effort)."""
    if not SUPABASE_ENABLED:
        return
    try:
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/{table}?{match_col}=eq.{match_val}",
            headers=_supa_headers(),
            json=data,
            timeout=10
        )
        if r.status_code in (200, 204):
            print(f"[SUPA] ✅ {table} UPDATE OK ({match_col}={match_val})")
        else:
            print(f"[SUPA] ⚠️ {table} UPDATE {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[SUPA] ❌ {table} UPDATE FAILED: {e}")


def _supa_async(func, *args):
    """Run Supabase operation in a background thread."""
    t = threading.Thread(target=func, args=args, daemon=True)
    t.start()


# ─── PUBLIC API (dual-write) ────────────────────────────────────────────────

def insert_reading(furnace, slave_id, temperature, raw_value=None, status="ok"):
    ts = _now()
    # SQLite (instant, always)
    conn = get_db()
    conn.execute(
        "INSERT INTO readings (timestamp, furnace, slave_id, temp_sales, raw_value, status) VALUES (?, ?, ?, ?, ?, ?)",
        (ts, furnace, slave_id, temperature, raw_value, status)
    )
    conn.commit()
    conn.close()

    # Supabase (async)
    _supa_async(_supa_insert, "readings", {
        "timestamp": ts,
        "furnace": furnace,
        "temp_sales": temperature or 0,
        "temp_cameras": 0
    })


def insert_event(event_type, furnace=None, details=None, email_sent=False):
    ts = _now()
    # SQLite
    conn = get_db()
    conn.execute(
        "INSERT INTO events (timestamp, event_type, furnace, details, email_sent) VALUES (?, ?, ?, ?, ?)",
        (ts, event_type, furnace, details, 1 if email_sent else 0)
    )
    conn.commit()
    conn.close()

    # Supabase (async)
    _supa_async(_supa_insert, "events", {
        "timestamp": ts,
        "event_type": event_type,
        "furnace": furnace,
        "details": details,
        "email_sent": email_sent
    })


def start_load(furnace, name=None, client_id=None, pieces_id=None, ot_number=None, required_min=120,
               check_set_point=None, temp_start=None, real_start_time=None):
    ts = _now()
    conn = get_db()
    if not name:
        count = conn.execute(
            "SELECT COUNT(*) FROM loads WHERE date = ? AND furnace = ?",
            (_today(), furnace)
        ).fetchone()[0]
        name = f"Carga {count + 1}"

    # SQLite - load
    conn.execute(
        """INSERT INTO loads (name, furnace, date, start_time, client_id, pieces_id,
           ot_number, duration_min, check_set_point, real_start_time, temp_start, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, furnace, _today(), ts, client_id, pieces_id, ot_number, required_min,
         check_set_point, real_start_time, temp_start,
         'active' if real_start_time else 'waiting_temp')
    )
    conn.commit()
    load_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # SQLite - work_order (if OT provided)
    if ot_number:
        conn.execute(
            "INSERT INTO work_orders (load_id, ot_number, required_min, start_time, status) VALUES (?, ?, ?, ?, 'active')",
            (load_id, ot_number, required_min, real_start_time or ts)
        )
        conn.commit()

    conn.close()

    # Supabase (async) — todos los campos
    _supa_async(_supa_insert, "loads", {
        "name": f"{name} [{furnace}]",
        "furnace": furnace,
        "date": _today(),
        "start_time": ts,
        "ot_number": ot_number or "",
        "duration_min": required_min,
        "status": "active" if real_start_time else "waiting_temp"
    })

    return load_id, name


def start_load_multi(furnace, subloads, check_set_point=None, temp_start=None, real_start_time=None):
    """Start a multi-subload session.
    Creates ONE loads row + ONE work_orders row per subload so all are visible in Cargas view.
    Returns (first_load_id, group_name, [work_order_ids])
    """
    ts = _now()
    initial_status = 'active' if real_start_time else 'waiting_temp'
    from datetime import datetime
    date_label = datetime.now().strftime("%d/%m/%y")

    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM loads WHERE date = ? AND furnace = ?",
        (_today(), furnace)
    ).fetchone()[0]

    first_load_id = None
    subload_ids = []

    for i, sub in enumerate(subloads):
        dur = sub.get("duration", 120)
        ot = sub.get("ot_number", "") or ""
        weight = sub.get("weight", "") or ""
        carga_num = count + 1 + i
        name = f"Carga {carga_num} {date_label}"

        # One loads row per subload
        conn.execute(
            """INSERT INTO loads (name, furnace, date, start_time, ot_number, duration_min,
               check_set_point, real_start_time, temp_start, weight, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, furnace, _today(), ts, ot, dur,
             check_set_point, real_start_time, temp_start, weight, initial_status)
        )
        conn.commit()
        load_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        if first_load_id is None:
            first_load_id = load_id

        # One work_order per subload
        conn.execute(
            """INSERT INTO work_orders
               (load_id, ot_number, required_min, duration_min, weight, start_time, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (load_id, ot, dur, dur, weight, real_start_time or ts, initial_status)
        )
        conn.commit()
        wo_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        subload_ids.append(wo_id)

        _supa_async(_supa_insert, "loads", {
            "name": name, "furnace": furnace, "date": _today(), "start_time": ts,
            "ot_number": ot, "duration_min": float(dur), "weight": weight,
            "status": initial_status
        })

    conn.close()
    group_name = f"Carga {count+1}+{len(subloads)} {date_label}"
    print(f"[DB] start_load_multi: {len(subloads)} loads created, work_orders={subload_ids}")
    return first_load_id, group_name, subload_ids

def update_real_start(load_id, temp_now):
    """Called when furnace temp reaches SP-10C. Updates all waiting_temp loads for the furnace."""
    ts = _now()
    conn = get_db()
    # Update by load_id
    conn.execute(
        "UPDATE loads SET real_start_time = ?, temp_start = ?, status = 'active' WHERE id = ? AND status = 'waiting_temp'",
        (ts, temp_now, load_id)
    )
    # Update all other waiting_temp loads for same furnace
    furnace_row = conn.execute("SELECT furnace FROM loads WHERE id = ?", (load_id,)).fetchone()
    if furnace_row:
        furnace = furnace_row["furnace"]
        conn.execute(
            "UPDATE loads SET real_start_time = ?, temp_start = ?, status = 'active' WHERE furnace = ? AND status = 'waiting_temp'",
            (ts, temp_now, furnace)
        )
        conn.execute(
            "UPDATE work_orders SET start_time = ?, status = 'active' WHERE load_id IN "
            "(SELECT id FROM loads WHERE furnace = ?) AND status = 'waiting_temp'",
            (ts, furnace)
        )
    conn.commit()
    row = conn.execute("SELECT check_set_point FROM loads WHERE id = ?", (load_id,)).fetchone()
    conn.close()
    sp = row["check_set_point"] if row else "?"
    print(f"[TEMP-CTRL] Load {load_id} real_start: temp={temp_now}C (SP={sp}C)")
    if SUPABASE_ENABLED:
        _supa_async(_supa_update, "loads", "status", "waiting_temp", {
            "status": "active"
        })
    return ts

def mark_subload_done(ot_id):
    """Mark a work_order as done and complete its parent loads row."""
    ts = _now()
    conn = get_db()
    conn.execute(
        "UPDATE work_orders SET done = 1, done_time = ?, end_time = ?, status = 'completed' WHERE id = ?",
        (ts, ts, ot_id)
    )
    conn.commit()

    row = conn.execute("SELECT load_id, ot_number FROM work_orders WHERE id = ?", (ot_id,)).fetchone()
    if row:
        load_id = row["load_id"]
        ot_number = row["ot_number"]
        load_row = conn.execute(
            "SELECT start_time, real_start_time FROM loads WHERE id = ?", (load_id,)
        ).fetchone()
        duration = 0
        total_minutes = 0.0
        if load_row:
            ref_time = load_row["real_start_time"] or load_row["start_time"]
            try:
                from datetime import datetime
                start_dt = datetime.fromisoformat(ref_time)
                now_dt = datetime.now(MADRID_TZ)
                duration = int((now_dt - start_dt).total_seconds())
                total_minutes = round(duration / 60.0, 2)
            except: pass
        conn.execute(
            "UPDATE loads SET status='completed', end_time=?, total_minutes=? "
            "WHERE id=? AND status IN ('active','waiting_temp')",
            (ts, total_minutes, load_id)
        )
        conn.commit()
        _supa_async(_supa_update, "work_orders", "ot_number", ot_number, {
            "done": True, "done_time": ts, "end_time": ts, "status": "completed"
        })
        _supa_async(_supa_update, "loads", "ot_number", ot_number, {
            "status": "completed", "end_time": ts,
            "total_minutes": total_minutes
        })
    conn.close()
    return True


def get_daily_loads_summary(date=None):
    """Get daily load summary with time ranges.
    Returns: list of dicts with load info formatted as:
    {index: '1/3', duration: "120'", time_range: '09:00 - 11:00', ...}
    """
    if date is None:
        date = _today()
    conn = get_db()
    # Get all loads for the date
    loads = conn.execute("""
        SELECT l.id, l.name, l.furnace, l.start_time, l.end_time, l.status,
               l.ot_number, l.duration_min
        FROM loads l
        WHERE l.date = ?
        ORDER BY l.start_time ASC
    """, (date,)).fetchall()
    total = len(loads)

    result = []
    for i, load in enumerate(loads):
        load_id = load["id"]
        # Get sub-loads for this load
        subs = conn.execute("""
            SELECT w.id, w.ot_number, w.duration_min, w.required_min,
                   w.weight, w.reference, w.start_time, w.end_time,
                   w.done, w.done_time, w.status
            FROM work_orders w WHERE w.load_id = ?
            ORDER BY w.id ASC
        """, (load_id,)).fetchall()

        # Format start/end times
        start_str = ''
        end_str = ''
        if load["start_time"]:
            try:
                st = datetime.fromisoformat(load["start_time"].replace('Z', '+00:00'))
                start_str = st.strftime('%H:%M')
            except: pass
        if load["end_time"]:
            try:
                et = datetime.fromisoformat(load["end_time"].replace('Z', '+00:00'))
                end_str = et.strftime('%H:%M')
            except: pass

        dur = load["duration_min"] or 0
        dur_label = f"{int(dur)}'" if dur >= 1 else f"{int(dur*60)}\"" 

        result.append({
            "index": f"{i+1}/{total}",
            "load_id": load_id,
            "name": load["name"],
            "furnace": load["furnace"],
            "ot_number": load["ot_number"],
            "duration": dur_label,
            "duration_min": dur,
            "time_range": f"{start_str} - {end_str}" if start_str else 'Sin hora',
            "start_time": load["start_time"],
            "end_time": load["end_time"],
            "status": load["status"],
            "subloads": [dict(s) for s in subs],
            "subload_count": len(subs)
        })

    conn.close()
    return result


def get_active_subloads(furnace, load_id=None):
    """Get active sub-loads for a furnace, filtered by load_id if provided."""
    conn = get_db()
    if load_id:
        rows = conn.execute("""
            SELECT w.id, w.ot_number, w.required_min, w.duration_min, w.weight, w.reference,
                   w.done, w.done_time, w.start_time, w.status, w.load_id,
                   l.name as load_name, l.start_time as load_start
            FROM work_orders w
            JOIN loads l ON l.id = w.load_id
            WHERE l.furnace = ? AND w.load_id = ?
            ORDER BY w.id ASC
        """, (furnace, load_id)).fetchall()
    else:
        rows = conn.execute("""
            SELECT w.id, w.ot_number, w.required_min, w.duration_min, w.weight, w.reference,
                   w.done, w.done_time, w.start_time, w.status, w.load_id,
                   l.name as load_name, l.start_time as load_start
            FROM work_orders w
            JOIN loads l ON l.id = w.load_id
            WHERE l.furnace = ? AND l.status = 'active'
            ORDER BY w.id ASC
        """, (furnace,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def cancel_orphaned_loads(furnace):
    """Cancel any active/waiting_temp loads for a furnace before starting a new one.
    Called when START is pressed to avoid stale loads polluting the UI.
    """
    ts = _now()
    conn = get_db()
    conn.execute(
        "UPDATE loads SET status = 'cancelled', end_time = ? WHERE furnace = ? AND status IN ('active', 'waiting_temp')",
        (ts, furnace)
    )
    conn.execute(
        "UPDATE work_orders SET status = 'cancelled' WHERE load_id IN "
        "(SELECT id FROM loads WHERE furnace = ? AND status = 'cancelled' AND end_time = ?)",
        (furnace, ts)
    )
    conn.commit()
    conn.close()
    print(f"[CANCEL] Orphaned loads cleared for {furnace}")


def get_next_ot_number():
    """Get the next OT number in format 'XX/YYYY' based on the last OT in DB."""
    import re
    year = datetime.now().year
    conn = get_db()
    # Find the highest OT number for the current year
    rows = conn.execute(
        "SELECT ot_number FROM work_orders WHERE ot_number IS NOT NULL ORDER BY id DESC LIMIT 200"
    ).fetchall()
    conn.close()

    max_num = 0
    pattern = re.compile(r'^(\d+)/' + str(year) + r'$')
    for row in rows:
        ot = row["ot_number"] or ""
        m = pattern.match(ot.strip())
        if m:
            num = int(m.group(1))
            if num > max_num:
                max_num = num

    next_num = max_num + 1
    return f"{next_num}/{year}"

def stop_load(furnace, temp_finish=None):
    ts = _now()
    conn = get_db()
    row = conn.execute(
        "SELECT id, start_time, real_start_time FROM loads WHERE furnace = ? AND status IN ('active', 'waiting_temp') ORDER BY id DESC LIMIT 1",
        (furnace,)
    ).fetchone()

    if row:
        # Use real_start_time for duration calculation if available
        ref_time = row["real_start_time"] or row["start_time"]
        start = datetime.fromisoformat(ref_time)
        now = datetime.now(MADRID_TZ)
        duration = int((now - start).total_seconds())

        total_minutes = round(duration / 60.0, 2)

        # SQLite
        conn.execute(
            "UPDATE loads SET end_time = ?, total_minutes = ?, temp_finish = ?, status = 'completed' WHERE id = ?",
            (ts, total_minutes, temp_finish, row["id"])
        )
        conn.commit()

        # Get the load name for Supabase matching
        load_row = conn.execute("SELECT name FROM loads WHERE id = ?", (row["id"],)).fetchone()
        load_name = load_row["name"] if load_row else None
        conn.close()

        # Supabase: update ALL active loads with end_time + duration + temp_finish
        if SUPABASE_ENABLED and load_name:
            def _supa_stop():
                try:
                    # Find ALL active/waiting loads
                    r = requests.get(
                        f"{SUPABASE_URL}/rest/v1/loads?status=in.(active,waiting_temp)&order=id.desc",
                        headers=_supa_headers(),
                        timeout=10
                    )
                    if r.status_code == 200 and r.json():
                        for supa_load in r.json():
                            supa_id = supa_load["id"]
                            _supa_update("loads", "id", supa_id, {
                                "end_time": ts,
                                "status": "completed",
                                "total_minutes": total_minutes
                            })
                        print(f"[SUPA] ✅ Stopped {len(r.json())} loads — {total_minutes}min")
                    else:
                        print(f"[SUPA] ⚠️ No active loads found to stop")
                except Exception as e:
                    print(f"[SUPA] ❌ stop_load FAILED: {e}")

            _supa_async(_supa_stop)

        return row["id"], duration

    conn.close()
    return None, 0


def get_waiting_temp_load(furnace):
    """Get the load that is waiting for temperature threshold."""
    conn = get_db()
    row = conn.execute(
        "SELECT id, check_set_point, start_time FROM loads WHERE furnace = ? AND status = 'waiting_temp' ORDER BY id DESC LIMIT 1",
        (furnace,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_stats():
    conn = get_db()
    readings_count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    loads_today = conn.execute("SELECT COUNT(*) FROM loads WHERE date = ?", (_today(),)).fetchone()[0]
    events_today = conn.execute("SELECT COUNT(*) FROM events WHERE timestamp >= ?", (_today(),)).fetchone()[0]
    conn.close()
    return {"readings": readings_count, "loads_today": loads_today, "events_today": events_today}


def get_loads(limit=50):
    conn = get_db()
    rows = conn.execute("SELECT * FROM loads ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_events(limit=50):
    conn = get_db()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_work_orders(limit=50):
    conn = get_db()
    rows = conn.execute("SELECT * FROM work_orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_traceability(limit=100):
    conn = get_db()
    rows = conn.execute("""
        SELECT
            l.id as load_id, l.name as load_name, l.furnace, l.date,
            l.start_time, l.end_time, l.total_minutes, l.status as load_status,
            w.id as ot_id, w.ot_number, w.client_id, w.client_name,
            w.piece_id, w.piece_ref, w.extra_id_1, w.extra_id_2, w.extra_id_3,
            w.required_min, w.process, w.status as ot_status
        FROM loads l
        LEFT JOIN work_orders w ON w.load_id = l.id
        ORDER BY l.id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_loads_history(date_from=None, date_to=None, furnace=None):
    """Get loads with optional filters for historical view."""
    conn = get_db()
    query = "SELECT * FROM loads WHERE 1=1"
    params = []
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)
    if furnace:
        query += " AND furnace = ?"
        params.append(furnace)
    query += " ORDER BY id DESC LIMIT 500"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_readings_for_load(load_id):
    """Get temperature readings for a specific load."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM readings WHERE timestamp >= (SELECT start_time FROM loads WHERE id = ?) "
        "AND timestamp <= COALESCE((SELECT end_time FROM loads WHERE id = ?), datetime('now')) "
        "ORDER BY timestamp",
        (load_id, load_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_daily_summary(days=30):
    """Get daily load counts and total duration for charts."""
    conn = get_db()
    rows = conn.execute("""
        SELECT date,
               COUNT(*) as total_loads,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
               COALESCE(SUM(total_minutes), 0) as total_duration_min
        FROM loads
        GROUP BY date
        ORDER BY date DESC
        LIMIT ?
    """, (days,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_loads_breakdown(days=30):
    """Get per-load duration breakdown grouped by date for stacked bar chart."""
    conn = get_db()
    rows = conn.execute("""
        SELECT date, id, name, furnace, total_minutes, status, ot_number
        FROM loads
        WHERE date >= date('now', ? || ' days')
        ORDER BY date ASC, id ASC
    """, (f"-{days}",)).fetchall()
    conn.close()

    # Group by date
    breakdown = {}
    for r in rows:
        d = dict(r)
        date = d["date"]
        if date not in breakdown:
            breakdown[date] = []
        breakdown[date].append({
            "id": d["id"],
            "name": d["name"],
            "furnace": d.get("furnace", ""),
            "ot_number": d.get("ot_number", ""),
            "duration_min": d.get("total_minutes") or 0,
            "total_minutes": d.get("total_minutes"),
            "status": d.get("status", "")
        })

    # Convert to sorted list
    result = [{"date": k, "loads": v} for k, v in sorted(breakdown.items())]
    return result


def search_loads(query_text):
    """Search loads by name, furnace, or date (for LLM results)."""
    conn = get_db()
    pattern = f"%{query_text}%"
    rows = conn.execute("""
        SELECT l.*, w.ot_number, w.client_name, w.piece_ref, w.process
        FROM loads l
        LEFT JOIN work_orders w ON w.load_id = l.id
        WHERE l.name LIKE ? OR l.furnace LIKE ? OR l.date LIKE ?
           OR w.ot_number LIKE ? OR w.client_name LIKE ?
        ORDER BY l.id DESC
        LIMIT 50
    """, (pattern, pattern, pattern, pattern, pattern)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_loads_for_date(date_str):
    """Get all loads for a specific date with OT info, ordered by start time."""
    conn = get_db()
    rows = conn.execute("""
        SELECT l.*,
               w.ot_number, w.client_id, w.client_name,
               w.piece_id, w.piece_ref, w.required_min, w.process,
               w.status as ot_status
        FROM loads l
        LEFT JOIN work_orders w ON w.load_id = l.id
        WHERE l.date = ?
        ORDER BY l.start_time ASC
    """, (date_str,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_load_detail(load_id):
    """Get full detail for a single load including readings stats."""
    conn = get_db()
    load = conn.execute("""
        SELECT l.*,
               w.ot_number, w.client_id, w.client_name,
               w.piece_id, w.piece_ref, w.required_min, w.process,
               w.extra_id_1, w.extra_id_2, w.extra_id_3,
               w.status as ot_status
        FROM loads l
        LEFT JOIN work_orders w ON w.load_id = l.id
        WHERE l.id = ?
    """, (load_id,)).fetchone()
    if not load:
        conn.close()
        return None

    result = dict(load)

    # Get readings stats for this load's time window
    if result.get("start_time"):
        end = result.get("end_time") or "9999-12-31"
        stats = conn.execute("""
            SELECT COUNT(*) as reading_count,
                   COALESCE(AVG(temp_sales), 0) as avg_temp_sales,
                   COALESCE(MIN(temp_sales), 0) as min_temp_sales,
                   COALESCE(MAX(temp_sales), 0) as max_temp_sales,
                   COALESCE(AVG(temp_cameras), 0) as avg_temp_cameras
            FROM readings
            WHERE furnace = ? AND timestamp >= ? AND timestamp <= ?
        """, (result.get("furnace", ""), result["start_time"], end)).fetchone()
        if stats:
            result.update(dict(stats))

    conn.close()
    return result


def get_dates_with_loads(month=None, year=None):
    """Get dates that have loads, with count per date, for calendar highlighting."""
    conn = get_db()
    query = "SELECT date, COUNT(*) as load_count FROM loads"
    params = []
    if month and year:
        query += " WHERE date LIKE ?"
        params.append(f"{year}-{month:02d}-%")
    query += " GROUP BY date ORDER BY date DESC LIMIT 90"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def record_temperature_snapshot(furnace, temperature):
    """Record a 30-minute temperature snapshot with active OT/subload context."""
    ts = _now()
    today = _today()
    conn = get_db()

    # Get active load info
    ot_number = ""
    subload_summary = ""
    load_status = "idle"

    active_load = conn.execute(
        "SELECT id, ot_number FROM loads WHERE furnace = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
        (furnace,)
    ).fetchone()

    if active_load:
        load_status = "active"
        ot_number = active_load["ot_number"] or ""
        subs = conn.execute(
            "SELECT ot_number, duration_min, weight, reference, done FROM work_orders WHERE load_id = ? ORDER BY id",
            (active_load["id"],)
        ).fetchall()
        if subs:
            summaries = []
            total = len(subs)
            for i, s in enumerate(subs):
                dur = s["duration_min"] or 0
                dur_label = f"{int(dur)}'" if dur >= 1 else f'{int(dur*60)}"'
                done_mark = "\u2713" if s["done"] else "\u23f3"
                summaries.append(f"{i+1}/{total} ({dur_label}) Ref:{s['reference'] or '-'} {done_mark}")
            subload_summary = " | ".join(summaries)

    conn.execute(
        "INSERT INTO temperature_tracking (timestamp, furnace, temperature, ot_number, subload_summary, load_status, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ts, furnace, temperature, ot_number, subload_summary, load_status, today)
    )
    conn.commit()
    conn.close()

    _supa_async(_supa_insert, "temperature_tracking", {
        "timestamp": ts, "furnace": furnace, "temperature": temperature or 0,
        "ot_number": ot_number, "subload_summary": subload_summary,
        "load_status": load_status, "date": today
    })


def get_temperature_range(date, hour_from=0, hour_to=23):
    """Get temperature readings for a date between two hours (for the graph)."""
    conn = get_db()
    # Use space-separated format (matches DB: '2026-03-25 09:00:00')
    ts_from_space = f"{date} {hour_from:02d}:00:00"
    ts_to_space = f"{date} {hour_to:02d}:59:59"
    # Also try T-separated format for safety
    ts_from_t = f"{date}T{hour_from:02d}:00:00"
    ts_to_t = f"{date}T{hour_to:02d}:59:59"

    rows = conn.execute("""
        SELECT timestamp, temp_sales as temperature, temp_cameras, furnace
        FROM readings
        WHERE ((timestamp >= ? AND timestamp <= ?) OR (timestamp >= ? AND timestamp <= ?))
        ORDER BY timestamp ASC
    """, (ts_from_space, ts_to_space, ts_from_t, ts_to_t)).fetchall()

    snapshots = conn.execute("""
        SELECT timestamp, temperature, ot_number, subload_summary, load_status
        FROM temperature_tracking
        WHERE date = ? AND ((timestamp >= ? AND timestamp <= ?) OR (timestamp >= ? AND timestamp <= ?))
        ORDER BY timestamp ASC
    """, (date, ts_from_space, ts_to_space, ts_from_t, ts_to_t)).fetchall()

    conn.close()
    return {
        "readings": [dict(r) for r in rows],
        "snapshots": [dict(s) for s in snapshots]
    }


# ─── ALARM THRESHOLDS & EVENTS ───────────────────────────────────────────────

def save_alarm_threshold(alarm_type, threshold):
    """Save or update an alarm threshold (sales/camaras). Dual-write."""
    conn = get_db()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO alarm_thresholds (type, threshold, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(type) DO UPDATE SET threshold=excluded.threshold, updated_at=excluded.updated_at
    """, (alarm_type, threshold, now))
    conn.commit()
    conn.close()
    # Supabase dual-write
    if SUPABASE_ENABLED:
        _supa_async(_supa_insert, "alarm_thresholds", {
            "type": alarm_type,
            "threshold": threshold,
            "updated_at": now
        })
    return True


def get_alarm_thresholds():
    """Get current alarm thresholds."""
    conn = get_db()
    rows = conn.execute("SELECT type, threshold FROM alarm_thresholds").fetchall()
    conn.close()
    return {r["type"]: r["threshold"] for r in rows}


def trigger_alarm_event(alarm_type, threshold, temperature):
    """Record an alarm event. Dual-write. Returns event ID."""
    conn = get_db()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute("""
        INSERT INTO alarm_events (type, threshold, temperature, triggered_at, status)
        VALUES (?, ?, ?, ?, 'active')
    """, (alarm_type, threshold, temperature, now))
    event_id = cur.lastrowid
    conn.commit()
    conn.close()
    # Supabase dual-write
    if SUPABASE_ENABLED:
        _supa_async(_supa_insert, "alarm_events", {
            "type": alarm_type,
            "threshold": threshold,
            "temperature": temperature,
            "triggered_at": now,
            "status": "active"
        })
    return event_id


def silence_alarm_event(event_id=None):
    """Silence active alarm events. If event_id given, silence that one; else all active."""
    conn = get_db()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if event_id:
        conn.execute("UPDATE alarm_events SET status='silenced', silenced_at=? WHERE id=?", (now, event_id))
    else:
        conn.execute("UPDATE alarm_events SET status='silenced', silenced_at=? WHERE status='active'", (now,))
    conn.commit()
    conn.close()
    return True


def resolve_alarm_events():
    """Mark active/silenced alarms as resolved (temp dropped below threshold)."""
    conn = get_db()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE alarm_events SET status='resolved', resolved_at=? WHERE status IN ('active','silenced')", (now,))
    conn.commit()
    conn.close()
    return True


def get_alarm_events(limit=50):
    """Get alarm event history."""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, type, threshold, temperature, triggered_at, silenced_at, resolved_at, status
        FROM alarm_events ORDER BY triggered_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    print(f"Stats: {get_stats()}")
    print(f"Supabase: {'ENABLED' if SUPABASE_ENABLED else 'DISABLED'}")
