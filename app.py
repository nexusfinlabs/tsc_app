#!/usr/bin/env python3
"""TSC Furnace Monitor — Web Application (Flask) + TASI TA612C"""
import os, json, time, threading, glob
try:
    import requests as _req
except ImportError:
    _req = None
from datetime import datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
    MADRID_TZ = ZoneInfo("Europe/Madrid")
except ImportError:
    MADRID_TZ = timezone(timedelta(hours=2))
from flask import Flask, request, jsonify, redirect, session, render_template_string, send_from_directory
from dotenv import load_dotenv
from page_restaurantes import RESTAURANTES_HTML

load_dotenv()

NOTIFY_OK = False
DB_OK = False

# ─── TASI TA612C Reader ──────────────────────────────────────────────────────
TASI_BAUD = 9600
TASI_CMD_VERSION  = b"\xAA\x55\x00\x03\x02"
TASI_CMD_REALTIME = b"\xAA\x55\x01\x03\x03"
TASI_DISCONNECTED = 28000
TASI_READ_INTERVAL = 30  # seconds between DB saves
TASI_CHANNEL_NAMES = {0: "test_1", 1: "test_2", 2: "sales", 3: "cameras"}
TASI_SERIAL_OK = False

try:
    import serial
    TASI_SERIAL_OK = True
except ImportError:
    print("[TASI] pyserial not installed — TASI reader disabled")

tasi_latest = {"CH1": None, "CH2": None, "CH3": None, "CH4": None,
               "status": "disconnected", "timestamp": None}
tasi_lock = threading.Lock()

def _find_tasi():
    if not TASI_SERIAL_OK:
        return None
    for port in sorted(glob.glob("/dev/ttyUSB*")):
        try:
            s = serial.Serial(port, TASI_BAUD, timeout=2,
                              xonxoff=False, rtscts=False, dsrdtr=False)
            s.dtr = True
            time.sleep(0.5)
            s.reset_input_buffer()
            s.write(TASI_CMD_VERSION)
            time.sleep(1)
            data = s.read(64)
            s.close()
            if data and len(data) >= 6 and data[0] == 0x55 and data[1] == 0xAA:
                return port
        except:
            continue
    return None

def _tasi_reader_thread():
    global tasi_latest
    ser = None
    while True:
        # Connect
        if ser is None or not ser.is_open:
            port = _find_tasi()
            if not port:
                with tasi_lock:
                    tasi_latest["status"] = "disconnected"
                time.sleep(5)
                continue
            try:
                ser = serial.Serial(port, TASI_BAUD, timeout=3,
                                    xonxoff=False, rtscts=False, dsrdtr=False)
                ser.dtr = True; ser.rts = True
                time.sleep(1)
                print(f"[TASI] ✅ Connected on {port}")
                with tasi_lock:
                    tasi_latest["status"] = f"connected ({port})"
            except:
                ser = None; time.sleep(5); continue

        # Read
        try:
            ser.reset_input_buffer()
            ser.write(TASI_CMD_REALTIME)
            time.sleep(1)
            data = ser.read(64)

            if data and len(data) >= 12 and data[0] == 0x55 and data[1] == 0xAA:
                now_local = datetime.now(MADRID_TZ).strftime("%Y-%m-%d %H:%M:%S")
                temps = {}
                for ch in range(4):
                    idx = 4 + (ch * 2)
                    raw = (data[idx + 1] << 8) | data[idx]
                    if raw == TASI_DISCONNECTED:
                        temps[f"CH{ch+1}"] = None
                    else:
                        if raw >= 0x8000:
                            raw -= 0x10000
                        temps[f"CH{ch+1}"] = round(raw / 10.0, 1)

                with tasi_lock:
                    tasi_latest.update({"timestamp": now_local, "status": "reading", **temps})

                # Update furnace temperatures (Sursulf 2 Energón = CH3 Sales)
                for f in FURNACES.values():
                    f["temperature"] = temps.get("CH3")

                # ── TEMP CONTROL: check if waiting loads can start ──
                for fname, f in FURNACES.items():
                    if f.get("waiting_for_temp") and f.get("load_id") and f.get("check_set_point"):
                        threshold = f["check_set_point"] - 10
                        current = temps.get("CH3")
                        if current is not None and current >= threshold:
                            # Temperature reached! Start countdown
                            f["waiting_for_temp"] = False
                            f["timer_running"] = True
                            f["start_time"] = time.time()
                            f["elapsed_seconds"] = 0
                            f["status"] = "ok"
                            print(f"[TEMP-CTRL] 🔥 TEMP REACHED! {current}°C >= {threshold}°C — countdown started!")
                            if DB_OK:
                                try:
                                    from database import update_real_start, insert_event
                                    real_ts = update_real_start(f["load_id"], current)
                                    insert_event("TEMP_REACHED", fname,
                                        f"🔥 {current}°C >= {threshold}°C (SP={f['check_set_point']}°C) — countdown started")
                                except Exception as e:
                                    print(f"[TEMP-CTRL] DB error: {e}")

                # Save to DB — controlled by Temp Tracker
                if DB_OK:
                    try:
                        from database import (get_db, _now, _supa_async, _supa_insert,
                                              SUPABASE_ENABLED, get_temp_tracker_state)
                        tracker = get_temp_tracker_state()
                        if tracker["enabled"]:
                            ts = _now()
                            conn = get_db()
                            conn.execute(
                                "INSERT INTO readings (timestamp, furnace, slave_id, temp_sales, temp_cameras, status) VALUES (?, ?, ?, ?, ?, ?)",
                                (ts, "sulfur_1", 0, temps.get("CH3"), temps.get("CH4"), "ok")
                            )
                            conn.commit()
                            conn.close()
                            # Supabase async
                            if SUPABASE_ENABLED:
                                _supa_async(_supa_insert, "readings", {
                                    "timestamp": ts,
                                    "furnace": "sulfur_1",
                                    "temp_sales": temps.get("CH3") or 0,
                                    "temp_cameras": temps.get("CH4") or 0
                                })
                            print(f"[TRACKER] ✅ Saved reading")
                    except Exception as e:
                        print(f"[TASI] DB save error: {e}")

                print(f"[TASI] CH1={temps.get('CH1')} CH2={temps.get('CH2')} CH3={temps.get('CH3')} CH4={temps.get('CH4')}")

            # Sleep based on tracker interval (or default 30s for live view)
            try:
                from database import get_temp_tracker_state
                tracker = get_temp_tracker_state()
                sleep_time = tracker["interval_s"] if tracker["enabled"] else TASI_READ_INTERVAL
            except:
                sleep_time = TASI_READ_INTERVAL
            time.sleep(sleep_time)

        except Exception as e:
            print(f"[TASI] Read error: {e}")
            ser = None
            time.sleep(5)

try:
    from database import (init_db, insert_event, start_load, stop_load, get_stats,
                          get_loads, get_events, get_work_orders, get_traceability,
                          get_loads_history, get_daily_summary, search_loads, get_db,
                          get_loads_for_date, get_load_detail, get_dates_with_loads,
                          get_readings_for_load, get_loads_breakdown,
                          start_load_multi, mark_subload_done, get_active_subloads,
                          get_next_ot_number, get_daily_loads_summary,
                          record_temperature_snapshot, get_temperature_range,
                          get_temp_tracker_state, set_temp_tracker,
                          save_llm_search, update_real_start, get_waiting_temp_load,
                          cancel_orphaned_loads,
                          save_alarm_threshold, get_alarm_thresholds,
                          trigger_alarm_event, silence_alarm_event,
                          resolve_alarm_events, get_alarm_events)
    DB_OK = True
except ImportError as e:
    print(f"[WARN] Database not available: {e}")

try:
    from notifier import notify_start, notify_stop
    NOTIFY_OK = True
except ImportError as e:
    print(f"[WARN] Notifier not available: {e}")
    def notify_start(*a, **k): pass
    def notify_stop(*a, **k): pass

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "tsc-secret-2026")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # HTTP+HTTPS mixed (LAN+Tailscale)
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24h session

# Serve sound files
@app.route("/sounds/<path:filename>")
def serve_sound(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), "sounds"), filename)

# ─── AUTH ─────────────────────────────────────────────────────────────────────
USERS = {
    "admin": os.getenv("ADMIN_PASS", "12341234"),
    "op1": "12341234",
    "op2": "12341234",
    "dario": "12341234",
    "alberto": "12341234",
}

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u, p = request.form.get("user", ""), request.form.get("pass", "")
        if USERS.get(u) == p:
            session.permanent = True  # Session lasts 24h
            session["user"] = u
            return redirect("/")
        return render_template_string(LOGIN_HTML, error="Credenciales incorrectas")
    return render_template_string(LOGIN_HTML, error="")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

def require_login(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

# ─── SETTINGS PERSISTENCE ─────────────────────────────────────────────────────
import json as _settings_json
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

def _load_settings():
    try:
        with open(SETTINGS_FILE) as fh:
            return _settings_json.load(fh)
    except Exception:
        return {}

def _save_settings(data):
    try:
        existing = _load_settings()
        existing.update(data)
        with open(SETTINGS_FILE, "w") as fh:
            _settings_json.dump(existing, fh)
    except Exception as e:
        print(f"[SETTINGS] Save error: {e}")

_settings = _load_settings()

# ─── FURNACE STATE ────────────────────────────────────────────────────────────
FURNACE_NAMES = ["sulfur_1"]
FURNACE_DISPLAY_NAMES = {"sulfur_1": "Sursulf 2 (Energón)"}  # display name → DB key unchanged
FURNACES = {}
for name in FURNACE_NAMES:
    _saved_sp = _settings.get(f"set_point_{name.strip()}")
    FURNACES[name.strip()] = {
        "name": FURNACE_DISPLAY_NAMES.get(name.strip(), name.strip()),
        "id": name.strip(), "temperature": None, "status": "idle",
        "target_seconds": int(os.getenv("DEFAULT_TIMER", "7200")),
        "elapsed_seconds": 0, "timer_running": False, "start_time": None,
        "load_id": None, "load_name": None, "ot_number": None, "subloads": [],
        "set_point": float(_saved_sp) if _saved_sp is not None else float(os.getenv("DEFAULT_SET_POINT", "570")),
        "waiting_for_temp": False, "check_set_point": None,
    }

def _timer_loop():
    while True:
        for f in FURNACES.values():
            if f["timer_running"] and f["start_time"] and not f.get("waiting_for_temp"):
                f["elapsed_seconds"] = int(time.time() - f["start_time"])
                if f["elapsed_seconds"] >= f["target_seconds"]:
                    f["status"] = "warning"
        time.sleep(1)

threading.Thread(target=_timer_loop, daemon=True).start()
if TASI_SERIAL_OK:
    threading.Thread(target=_tasi_reader_thread, daemon=True).start()
    print("[TASI] 🔥 Reader thread started")

# ─── API ENDPOINTS ────────────────────────────────────────────────────────────
@app.route("/")
@require_login
def index():
    return open("index.html").read()

@app.route("/api/status")
def api_status():
    return jsonify({
        "furnaces": list(FURNACES.values()),
        "updated_at": datetime.now().strftime("%H:%M:%S"),
        "connection_ok": True
    })

@app.route("/api/set-point/<furnace>", methods=["POST"])
@require_login
def api_set_point(furnace):
    f = FURNACES.get(furnace)
    if not f: return jsonify({"error": "Unknown furnace"}), 404
    data = request.json or {}
    sp = data.get("set_point")
    if sp is not None:
        f["set_point"] = float(sp)
        _save_settings({f"set_point_{furnace}": float(sp)})  # persist to disk
        if f.get("waiting_for_temp"):
            f["check_set_point"] = float(sp)
            print(f"[SET-POINT] {furnace} = {f['set_point']}°C — updated check_set_point (waiting)")
        else:
            print(f"[SET-POINT] {furnace} = {f['set_point']}°C — saved to settings.json")
    return jsonify({"ok": True, "set_point": f["set_point"]})

@app.route("/api/set-point/<furnace>")
def api_get_set_point(furnace):
    f = FURNACES.get(furnace)
    if not f: return jsonify({"error": "Unknown furnace"}), 404
    return jsonify({"set_point": f.get("set_point", 570)})

@app.route("/api/timer/<furnace>/start", methods=["POST"])
@require_login
def timer_start(furnace):
    f = FURNACES.get(furnace)
    if not f: return jsonify({"error": "Unknown furnace"}), 404
    data = request.json or {}
    duration_min = data.get("duration", 120)
    ot_number = data.get("ot_number", "")
    f["target_seconds"] = int(duration_min) * 60
    f["status"] = "ok"; f["timer_running"] = True; f["start_time"] = time.time(); f["elapsed_seconds"] = 0
    if DB_OK:
        load_id, load_name = start_load(furnace, ot_number=ot_number, required_min=int(duration_min))
        f["load_id"] = load_id; f["load_name"] = load_name; f["ot_number"] = ot_number
        insert_event("LOAD_START", furnace, f"Started {load_name} | OT: {ot_number} | {duration_min}min")
        try: notify_start(furnace, load_name, ot_number=ot_number, duration_min=int(duration_min), temperature=f.get('temperature'))
        except Exception as e: print(f'[NOTIFY] Error: {e}')
    return jsonify({"ok": True})

@app.route("/api/timer/<furnace>/stop", methods=["POST"])
@require_login
def timer_stop(furnace):
    f = FURNACES.get(furnace)
    if not f: return jsonify({"error": "Unknown furnace"}), 404
    f["status"] = "idle"; f["timer_running"] = False; f["waiting_for_temp"] = False
    temp_finish = f.get("temperature")
    if DB_OK and f.get("load_id"):
        load_id, duration = stop_load(furnace, temp_finish=temp_finish)
        insert_event("LOAD_STOP", furnace, f"Stopped {f.get('load_name','')} - {duration}s | temp_finish={temp_finish}°C")
        try: notify_stop(furnace, f.get('load_name', ''), duration, ot_number=f.get('ot_number', ''))
        except Exception as e: print(f'[NOTIFY] Error: {e}')
    f["load_id"] = None; f["load_name"] = None; f["ot_number"] = None
    f["subloads"] = []; f["check_set_point"] = None
    return jsonify({"ok": True})

@app.route("/api/timer/<furnace>/start-multi", methods=["POST"])
@require_login
def timer_start_multi(furnace):
    f = FURNACES.get(furnace)
    if not f: return jsonify({"error": "Unknown furnace"}), 404
    data = request.json or {}
    subloads = data.get("subloads", [])
    if not subloads: return jsonify({"error": "No subloads provided"}), 400
    max_duration = max(s.get("duration", 120) for s in subloads)
    f["target_seconds"] = int(float(max_duration) * 60)

    # Temperature control: check if temp is within set_point - 10
    set_point = f.get("set_point", 570)
    current_temp = f.get("temperature")
    threshold = set_point - 10
    force_start = data.get("force_start", False)  # START=True (immediate), AUTO=False (wait for temp)
    temp_ok = force_start or (current_temp is not None and current_temp >= threshold)

    from database import _now
    real_start = _now() if temp_ok else None
    temp_at_start = current_temp if temp_ok else None

    if temp_ok:
        # Temp is OK — start countdown immediately
        f["status"] = "ok"; f["timer_running"] = True; f["start_time"] = time.time(); f["elapsed_seconds"] = 0
        f["waiting_for_temp"] = False
        print(f"[TEMP-CTRL] ✅ Temp {current_temp}°C >= {threshold}°C — countdown starts NOW")
    else:
        # Temp too low — wait for it to reach threshold
        f["status"] = "ok"; f["timer_running"] = False; f["start_time"] = None; f["elapsed_seconds"] = 0
        f["waiting_for_temp"] = True
        print(f"[TEMP-CTRL] 🟡 Temp {current_temp}°C < {threshold}°C — WAITING for temperature")

    f["check_set_point"] = set_point

    if DB_OK:
        # Cancel any orphaned active loads before creating the new one
        try: cancel_orphaned_loads(furnace)
        except Exception as e: print(f"[CANCEL] Error: {e}")
        load_id, load_name, sub_ids = start_load_multi(
            furnace, subloads,
            check_set_point=set_point,
            temp_start=temp_at_start,
            real_start_time=real_start
        )
        f["load_id"] = load_id; f["load_name"] = load_name
        f["ot_number"] = subloads[0].get("ot_number", "")
        f["subloads"] = [{"id": sid, **sub} for sid, sub in zip(sub_ids, subloads)]
        details = " | ".join([f"{s.get('ot_number','?')} {s.get('duration',0)}min {s.get('weight','')}kg" for s in subloads])
        status_msg = "STARTED" if temp_ok else f"WAITING TEMP ({current_temp or '?'}°C < {threshold}°C)"
        insert_event("LOAD_START_MULTI", furnace, f"{status_msg} {load_name} | SP={set_point}°C | {details}")
        try: notify_start(furnace, load_name, ot_number=f["ot_number"], duration_min=int(max_duration), temperature=f.get('temperature'))
        except Exception as e: print(f'[NOTIFY] Error: {e}')
    return jsonify({
        "ok": True,
        "load_id": f.get("load_id"),
        "subload_ids": [s["id"] for s in f.get("subloads", [])],
        "waiting_for_temp": f["waiting_for_temp"],
        "threshold": threshold,
        "current_temp": current_temp
    })

@app.route("/api/subload/<int:ot_id>/done", methods=["POST"])
@require_login
def subload_done(ot_id):
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    mark_subload_done(ot_id)
    insert_event("SUBLOAD_DONE", None, f"Sub-load {ot_id} marked as done/withdrawn")

    # Mark as done in memory so the countdown row shows ✓ Retirado
    for fname, f in FURNACES.items():
        for s in f.get("subloads", []):
            if s.get("id") == ot_id:
                s["done"] = 1

    # Auto-stop: only when ALL in-memory subloads are done
    for fname, f in FURNACES.items():
        if f.get("timer_running") or f.get("waiting_for_temp"):
            mem_subs = f.get("subloads", [])
            all_done = len(mem_subs) > 0 and all(s.get("done") == 1 for s in mem_subs)
            if all_done:
                print(f"[AUTO-STOP] All {len(mem_subs)} subloads done — stopping {fname}")
                f["status"] = "idle"; f["timer_running"] = False; f["waiting_for_temp"] = False
                temp_finish = f.get("temperature")
                insert_event("LOAD_STOP", fname, f"Auto-stopped {f.get('load_name','')} — all subloads done | temp={temp_finish}°C")
                f["load_id"] = None; f["load_name"] = None; f["ot_number"] = None
                f["subloads"] = []; f["check_set_point"] = None

    return jsonify({"ok": True})

@app.route("/api/subloads/<furnace>")
def api_subloads(furnace):
    if not DB_OK: return jsonify([])
    # Return ALL active subloads for the furnace (no load_id filter)
    return jsonify(get_active_subloads(furnace))

@app.route("/api/next-ot")
def api_next_ot():
    if not DB_OK:
        from datetime import datetime
        return jsonify({"next_ot": f"1/{datetime.now().year}"})
    return jsonify({"next_ot": get_next_ot_number()})

@app.route("/api/daily-loads")
def api_daily_loads():
    if not DB_OK: return jsonify([])
    date = request.args.get('date', None)
    return jsonify(get_daily_loads_summary(date))

@app.route("/api/readings/recent")
def api_readings_recent():
    """Return readings from the last N minutes + current TASI live reading."""
    minutes = int(request.args.get('minutes', 5))
    minutes = max(1, min(minutes, 1440))
    result = {"readings": [], "live": None}
    
    # Live TASI data
    with tasi_lock:
        live = dict(tasi_latest)
    if live.get("CH3") is not None or live.get("CH4") is not None:
        result["live"] = {
            "timestamp": live.get("timestamp", ""),
            "temp_sales": live.get("CH3"),
            "temp_cameras": live.get("CH4"),
        }
    
    # DB readings from last N minutes
    if DB_OK:
        try:
            conn = get_db()
            # Calculate cutoff in Madrid time
            from datetime import timedelta
            cutoff = (datetime.now(MADRID_TZ) - timedelta(minutes=minutes)).isoformat()
            rows = conn.execute(
                """SELECT timestamp, temp_sales, temp_cameras 
                   FROM readings 
                   WHERE timestamp >= ?
                   ORDER BY timestamp ASC""",
                (cutoff,)
            ).fetchall()
            result["readings"] = [dict(r) for r in rows]
            conn.close()
        except Exception as e:
            print(f"[API] readings/recent error: {e}")
    
    # If no DB readings, include live point so chart always shows something
    if not result["readings"] and result["live"]:
        result["readings"] = [result["live"]]
    
    return jsonify(result)

@app.route("/api/temperature-graph")
def api_temperature_graph():
    if not DB_OK: return jsonify({"readings": [], "snapshots": []})
    date = request.args.get('date')
    hour_from = int(request.args.get('from', 0))
    hour_to = int(request.args.get('to', 23))
    if not date:
        from datetime import datetime
        date = datetime.now().strftime('%Y-%m-%d')
    return jsonify(get_temperature_range(date, hour_from, hour_to))

@app.route("/api/temp-tracker", methods=["GET"])
def api_temp_tracker_status():
    if not DB_OK:
        return jsonify({"enabled": False, "interval_s": 60})
    return jsonify(get_temp_tracker_state())

@app.route("/api/temp-tracker", methods=["POST"])
@require_login
def api_temp_tracker_update():
    if not DB_OK:
        return jsonify({"error": "DB not available"}), 500
    data = request.json or {}
    state = set_temp_tracker(
        enabled=data.get("enabled"),
        interval_s=data.get("interval_s")
    )
    insert_event("TEMP_TRACKER", "sulfur_1",
                 f"Tracker {'ON' if state['enabled'] else 'OFF'} — {state['interval_s']}s")
    return jsonify(state)

@app.route("/api/timer/<furnace>/reset", methods=["POST"])
@require_login
def timer_reset(furnace):
    """Hard reset: clears in-memory state ONLY. No DB write.
    Use to cancel a load entered with wrong OT/data before committing.
    """
    f = FURNACES.get(furnace)
    if not f: return jsonify({"error": "Unknown furnace"}), 404
    # Clear all in-memory state — no DB write
    f["status"] = "idle"
    f["timer_running"] = False
    f["waiting_for_temp"] = False
    f["elapsed_seconds"] = 0
    f["start_time"] = None
    f["load_id"] = None
    f["load_name"] = None
    f["ot_number"] = None
    f["subloads"] = []
    f["check_set_point"] = None
    print(f"[RESET] ↺ {furnace} reset to idle (no DB write)")
    return jsonify({"ok": True})


@app.route("/api/reading", methods=["POST"])
def api_reading():
    data = request.json
    if DB_OK:
        from database import save_reading
        save_reading(data)
        furnace = data.get("furnace", "")
        if furnace in FURNACES:
            FURNACES[furnace]["temperature"] = data.get("temp_sales")
    return jsonify({"ok": True})

@app.route("/api/tasi")
def api_tasi():
    with tasi_lock:
        return jsonify(tasi_latest)

# ─── MAINTENANCE SCHEDULE ─────────────────────────────────────────────────────
MAINTENANCE_SCHEDULE = [
    {"name": "Análisis de Sales", "every": 20, "color": "#22d3ee"},
    {"name": "Desenfangar",        "every": 15, "color": "#22c55e"},
    {"name": "Control de Tª",      "every": 10, "color": "#ef4444"},
    {"name": "Probetas",           "every": 0,  "color": "#e2e8f0"},  # manual
]

# Store last control dates in a JSON file
import json as _json
MAINT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "maintenance.json")

def _load_maint_dates():
    try:
        with open(MAINT_FILE, "r") as f:
            return _json.load(f)
    except:
        return {}

def _save_maint_dates(data):
    os.makedirs(os.path.dirname(MAINT_FILE), exist_ok=True)
    with open(MAINT_FILE, "w") as f:
        _json.dump(data, f, indent=2)

def _get_pv_threshold():
    """Punto de Vigilancia = set_point - 10°C from furnace config."""
    furnace = FURNACES.get("sulfur_1", {})
    sp = furnace.get("set_point", 570)
    return sp - 10

def _count_pv_days_since(since_date_str):
    """Count unique days where temp_sales reached PV (set_point-10°C) after since_date.
    
    A day 'counts' only when the furnace was active and reached the Punto de Vigilancia.
    Max 1 count per calendar day regardless of how many readings qualify.
    """
    if not DB_OK:
        return 0
    pv = _get_pv_threshold()
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT DISTINCT date(timestamp) FROM readings "
            "WHERE temp_sales >= ? AND date(timestamp) > ? ORDER BY date(timestamp)",
            (pv, since_date_str)
        ).fetchall()
        conn.close()
        return len(rows)
    except:
        return 0

def _count_load_days_since(since_date_str):
    """Legacy: kept for backward compat. Now delegates to PV-based counter."""
    return _count_pv_days_since(since_date_str)

def _get_next_control_date(since_date_str, every_n_load_days):
    """Estimate next control date: find the Nth future load-day after since_date."""
    if not DB_OK or every_n_load_days <= 0:
        return None
    load_days_since = _count_load_days_since(since_date_str)
    remaining = every_n_load_days - load_days_since
    if remaining <= 0:
        return "¡HOY!"
    # Estimate: ~5 load-days per week (Mon-Fri), so remaining * 7/5 calendar days
    from datetime import datetime, timedelta
    today = datetime.now().date()
    est_days = int(remaining * 7 / 5)
    est_date = today + timedelta(days=est_days)
    # Skip weekends
    while est_date.weekday() >= 5:
        est_date += timedelta(days=1)
    return est_date.strftime("%d/%m/%y")

@app.route("/api/maintenance")
def api_maintenance():
    total_loads = 0
    if DB_OK:
        try:
            conn = get_db()
            total_loads = conn.execute("SELECT COUNT(*) FROM loads WHERE status='completed'").fetchone()[0]
            conn.close()
        except: pass

    maint_dates = _load_maint_dates()
    pv = _get_pv_threshold()
    tasks = []
    for m in MAINTENANCE_SCHEDULE:
        last_date = maint_dates.get(m["name"])
        if m["every"] > 0 and last_date:
            pv_days = _count_pv_days_since(last_date)
            remaining = max(0, m["every"] - pv_days)
            due = remaining <= 0
            next_date = _get_next_control_date(last_date, m["every"])
            tasks.append({
                "name": m["name"], "every": m["every"], "color": m["color"],
                "loads_since": pv_days, "remaining": remaining, "due": due,
                "last_date": last_date, "next_date": next_date,
                "pv_threshold": pv
            })
        elif m["every"] > 0:
            # No reset date set yet — count all PV days ever recorded
            try:
                conn = get_db()
                total_days = conn.execute(
                    "SELECT COUNT(DISTINCT date(timestamp)) FROM readings WHERE temp_sales >= ?",
                    (pv,)
                ).fetchone()[0]
                conn.close()
            except: total_days = 0
            pv_days = total_days % m["every"]
            remaining = m["every"] - pv_days
            due = remaining == m["every"] or remaining <= 0
            tasks.append({
                "name": m["name"], "every": m["every"], "color": m["color"],
                "loads_since": pv_days,
                "remaining": remaining if remaining != m["every"] else 0, "due": due,
                "last_date": None, "next_date": None, "pv_threshold": pv
            })
        else:
            tasks.append({
                "name": m["name"], "every": 0, "color": m["color"],
                "loads_since": 0, "remaining": 0, "due": False,
                "last_date": last_date, "next_date": None, "pv_threshold": pv
            })
    today_tasks = [t for t in tasks if t["due"]]
    return jsonify({"total_loads": total_loads, "tasks": tasks, "today": today_tasks})

@app.route("/api/maintenance/reset", methods=["POST"])
@require_login
def api_maintenance_reset():
    """Reset a maintenance task counter to 0 — sets last_date=today so it starts counting PV days from scratch."""
    data = request.get_json() or {}
    task_name = data.get("task", "")
    valid_names = [m["name"] for m in MAINTENANCE_SCHEDULE]
    if task_name not in valid_names:
        return jsonify({"error": "unknown task"}), 400
    today = datetime.now(MADRID_TZ).strftime("%Y-%m-%d")
    # Validate task exists
    valid_names = [m["name"] for m in MAINTENANCE_SCHEDULE]
    if task_name not in valid_names:
        return jsonify({"error": f"Unknown task: {task_name}"}), 400
    maint_dates = _load_maint_dates()
    maint_dates[task_name] = today
    _save_maint_dates(maint_dates)
    pv = _get_pv_threshold()
    print(f"[MAINT] ↺ Reset '{task_name}' → last_date={today}, PV={pv}°C (counting from 0)")
    return jsonify({"ok": True, "task": task_name, "reset_to": today, "pv_threshold": pv})

@app.route("/api/maintenance/adjust", methods=["POST"])
@require_login
def api_maintenance_adjust():
    """Legacy endpoint — kept for backward compat. Use /reset for new UI."""
    data = request.get_json() or {}
    task_name = data.get("task", "")
    last_date = data.get("last_date", "")
    if not task_name or not last_date:
        return jsonify({"error": "task and last_date required"}), 400
    valid_names = [m["name"] for m in MAINTENANCE_SCHEDULE]
    if task_name not in valid_names:
        return jsonify({"error": "unknown task"}), 400
    maint_dates = _load_maint_dates()
    maint_dates[task_name] = last_date
    _save_maint_dates(maint_dates)
    print(f"[MAINT] ✅ Adjusted '{task_name}' → last control: {last_date}")
    return jsonify({"ok": True, "task": task_name, "last_date": last_date})


# ─── ALARM API ────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TSC_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7024795874")

def _send_telegram_alert(message):
    """Send alarm notification via Telegram bot (fire-and-forget in background)."""
    if not TELEGRAM_BOT_TOKEN:
        print("[ALARM] No Telegram token, skipping notification")
        return
    def _send():
        try:
            import requests as rq
            rq.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"},
                timeout=10
            )
            print(f"[ALARM] Telegram notification sent")
        except Exception as e:
            print(f"[ALARM] Telegram notification failed: {e}")
    import threading
    threading.Thread(target=_send, daemon=True).start()


@app.route("/api/alarm/thresholds")
@require_login
def api_alarm_thresholds():
    if not DB_OK: return jsonify({}), 500
    return jsonify(get_alarm_thresholds())


@app.route("/api/alarm/threshold", methods=["POST"])
@require_login
def api_alarm_threshold_save():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    data = request.get_json() or {}
    atype = data.get("type", "")
    threshold = data.get("threshold")
    if atype not in ("sales", "camaras") or threshold is None:
        return jsonify({"error": "type (sales/camaras) and threshold required"}), 400
    save_alarm_threshold(atype, float(threshold))
    print(f"[ALARM] Threshold saved: {atype} >= {threshold}°C")
    return jsonify({"ok": True, "type": atype, "threshold": threshold})


@app.route("/api/alarm/trigger", methods=["POST"])
@require_login
def api_alarm_trigger():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    data = request.get_json() or {}
    atype = data.get("type", "")
    threshold = data.get("threshold", 0)
    temperature = data.get("temperature", 0)
    if atype not in ("sales", "camaras"):
        return jsonify({"error": "type must be sales or camaras"}), 400
    event_id = trigger_alarm_event(atype, float(threshold), float(temperature))
    # Telegram notification
    emoji = "🔥" if atype == "sales" else "❄️"
    label = "Sales" if atype == "sales" else "Cámaras"
    _send_telegram_alert(
        f"🚨 *ALARMA TSC - {label}*\n\n"
        f"{emoji} Temperatura: *{temperature}°C*\n"
        f"⚠️ Umbral: *{threshold}°C*\n"
        f"🕐 {datetime.now(MADRID_TZ).strftime('%d/%m/%Y %H:%M:%S')}"
    )
    return jsonify({"ok": True, "event_id": event_id})


@app.route("/api/alarm/silence", methods=["POST"])
@require_login
def api_alarm_silence():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    data = request.get_json() or {}
    event_id = data.get("event_id")
    silence_alarm_event(event_id)
    return jsonify({"ok": True})


@app.route("/api/alarm/resolve", methods=["POST"])
@require_login
def api_alarm_resolve():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    resolve_alarm_events()
    return jsonify({"ok": True})


@app.route("/api/alarm/events")
@require_login
def api_alarm_events():
    if not DB_OK: return jsonify([]), 500
    limit = request.args.get("limit", 50, type=int)
    return jsonify(get_alarm_events(limit))


# ─── DB API ENDPOINTS ────────────────────────────────────────────────────────
@app.route("/api/db/stats")
def db_stats():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    return jsonify(get_stats())

@app.route("/api/db/loads")
def db_loads():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    return jsonify(get_loads())

@app.route("/api/db/events")
def db_events():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    return jsonify(get_events())

@app.route("/api/db/ots")
def db_ots():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    return jsonify(get_work_orders())

@app.route("/api/db/traceability")
def db_traceability():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    return jsonify(get_traceability())

@app.route("/api/db/daily-summary")
def db_daily_summary():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    days = request.args.get("days", 30, type=int)
    return jsonify(get_daily_summary(days))

@app.route("/api/db/calendar-dates")
def db_calendar_dates():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    return jsonify(get_dates_with_loads(month, year))

@app.route("/api/db/loads-by-date")
def db_loads_by_date():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    date = request.args.get("date", "")
    if not date: return jsonify([])
    return jsonify(get_loads_for_date(date))

@app.route("/api/db/load/<int:load_id>")
def db_load_detail(load_id):
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    detail = get_load_detail(load_id)
    if not detail: return jsonify({"error": "Load not found"}), 404
    return jsonify(detail)

@app.route("/api/db/load/<int:load_id>/readings")
def db_load_readings(load_id):
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    readings = get_readings_for_load(load_id)
    return jsonify(readings)

@app.route("/api/db/loads-breakdown")
def db_loads_breakdown():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    days = request.args.get("days", 30, type=int)
    return jsonify(get_loads_breakdown(days))

@app.route("/api/db/loads-history")
def db_loads_history():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    return jsonify(get_loads_history(
        request.args.get("from"), request.args.get("to"), request.args.get("furnace")))

@app.route("/api/db/search")
def db_search():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    q = request.args.get("q", "")
    return jsonify(search_loads(q) if q else [])

@app.route("/api/llm/query", methods=["POST"])
def llm_query():
    if not DB_OK: return jsonify({"error": "DB not available"}), 500
    data = request.json or {}
    q = data.get("query", "")
    results = search_loads(q)
    return jsonify({"query": q, "results": results, "results_count": len(results),
                    "message": f"Encontradas {len(results)} cargas para '{q}'"})

# ─── DASHBOARD PAGE ──────────────────────────────────────────────────────────
@app.route("/dashboard")
@require_login
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route("/monitor")
@require_login
def monitor():
    return render_template_string(MONITOR_HTML)

@app.route("/db")
@require_login
def db_viewer():
    return render_template_string(DB_VIEWER_HTML)

# ─── /crm → BB4x4 CRM full frontend with static assets ──────────────────────
CRM_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crm_static")

@app.route("/crm/static/<path:filename>")
def crm_static(filename):
    return send_from_directory(CRM_STATIC_DIR, filename)

@app.route("/crm/vehicle/<path:slug>")
def page_crm_vehicle(slug):
    html_path = os.path.join(CRM_STATIC_DIR, "vehicle.html")
    if os.path.exists(html_path):
        with open(html_path) as f:
            return _Response(f.read(), mimetype='text/html')
    return _Response("<h1>Vehicle not found</h1>", mimetype='text/html', status=404)

@app.route("/crm")
def page_crm():
    html_path = os.path.join(CRM_STATIC_DIR, "index.html")
    if os.path.exists(html_path):
        with open(html_path) as f:
            return _Response(f.read(), mimetype='text/html')
    return _Response("<h1>CRM not found</h1>", mimetype='text/html', status=404)

@app.route("/restaurantes")
def page_restaurantes():
    return _Response(RESTAURANTES_HTML, mimetype='text/html')

# ─── /medical → redirect to Streamlit on port 8443 (full WebSocket support) ──
@app.route("/medical", defaults={"path": ""})
@app.route("/medical/<path:path>")
def proxy_medical(path):
    # Tailscale Funnel on :8443 serves Streamlit directly (WebSocket works)
    host = request.host.split(':')[0]  # strip port
    return redirect(f"https://{host}:8443/{path}", code=302)

# ─── LOGIN HTML ───────────────────────────────────────────────────────────────
LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TSC Login</title>
<style>
body{margin:0;font-family:'Segoe UI',system-ui,sans-serif;background:#0a0a0f;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh}
.login{background:linear-gradient(135deg,#0f172a,#1e1b4b);padding:40px;border-radius:20px;border:1px solid #2a2a3e;width:320px}
h1{text-align:center;margin-bottom:30px;background:linear-gradient(135deg,#22c55e,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
input{width:100%;padding:12px;margin:8px 0;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:14px;box-sizing:border-box}
button{width:100%;padding:12px;margin-top:16px;background:#22c55e;border:none;border-radius:8px;color:#fff;font-size:16px;font-weight:600;cursor:pointer}
.error{color:#ef4444;text-align:center;margin-top:10px;font-size:13px}
</style>
</head>
<body>
<div class="login">
<h1>TSC Monitor</h1>
<form method="POST">
<input name="user" placeholder="Usuario" required>
<input name="pass" type="password" placeholder="Contrasena" required>
<button type="submit">Entrar</button>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
</form>
</div>
</body>
</html>"""

# ─── MONITOR HTML (Thermal Dashboard) ────────────────────────────────────────
MONITOR_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TSC — Monitor Térmico</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#0a0e1a;color:#e0e6ed;min-height:100vh}
.topbar{background:linear-gradient(135deg,#0f172a,#1e1b4b);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #2a2a3e;position:sticky;top:0;z-index:100}
.topbar h1{font-size:22px;background:linear-gradient(135deg,#22c55e,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.topbar .links{display:flex;gap:4px}
.topbar .links a{color:#64748b;text-decoration:none;padding:6px 12px;font-size:14px;border-radius:6px;transition:all .2s}
.topbar .links a:hover{color:#e2e8f0;background:rgba(255,255,255,.05)}
.topbar .links a.active{color:#22c55e;font-weight:600}
.topbar .links .logout{color:#ef4444;margin-left:12px;border:1px solid rgba(239,68,68,.3)}
.status-bar{display:flex;justify-content:center;align-items:center;gap:10px;padding:8px;font-size:13px}
.pulse{display:inline-block;width:8px;height:8px;border-radius:50%;animation:pulse 2s infinite}
.pulse.green{background:#48bb78}.pulse.red{background:#f56565}.pulse.yellow{background:#ecc94b}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.2rem;padding:1.5rem;max-width:1200px;margin:0 auto}
.card{background:linear-gradient(145deg,#161b33,#1a2040);border:1px solid rgba(99,179,237,.15);border-radius:16px;padding:1.5rem;position:relative;overflow:hidden;transition:transform .3s,box-shadow .3s}
.card:hover{transform:translateY(-3px);box-shadow:0 12px 40px rgba(99,179,237,.15)}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:16px 16px 0 0}
.card.ch1::before{background:linear-gradient(90deg,#f56565,#ed8936)}
.card.ch2::before{background:linear-gradient(90deg,#4fd1c5,#38b2ac)}
.card.ch3::before{background:linear-gradient(90deg,#22D3EE,#0ea5e9)}
.card.ch4::before{background:linear-gradient(90deg,#f97316,#ea6c0a)}
.card-label{font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:#718096;margin-bottom:.6rem}
.card-temp{font-family:'JetBrains Mono',monospace;font-size:2.8rem;font-weight:700;line-height:1;margin-bottom:.3rem}
.card.ch1 .card-temp{color:#f56565}.card.ch2 .card-temp{color:#4fd1c5}
.card.ch3 .card-temp{color:#22D3EE}.card.ch4 .card-temp{color:#f97316}
.card-temp.disconnected{color:#4a5568;font-size:2rem}
.card-unit{font-size:1.2rem;color:#718096}
.timestamp{text-align:center;padding:.8rem;color:#4a5568;font-family:'JetBrains Mono',monospace;font-size:.8rem}
.chart-container{max-width:1200px;margin:0 auto;padding:0 1.5rem 1.5rem}
.chart-card{background:linear-gradient(145deg,#161b33,#1a2040);border:1px solid rgba(99,179,237,.15);border-radius:16px;padding:1.5rem}
.chart-card h2{font-size:.95rem;color:#94a3b8;margin-bottom:1rem;font-weight:600}
canvas{width:100%!important;min-height:300px}
</style>
</head>
<body>
<div class="topbar">
  <h1>TSC — Monitor Térmico</h1>
  <div class="links">
    <a href="/">Control</a>
    <a href="/monitor" class="active">Monitor</a>
    <a href="/dashboard">Dashboard</a>
    <a href="/db">Base de Datos</a>
    <a href="/llm">LLM</a>
    <a href="/logout" class="logout">Salir</a>
  </div>
</div>
<div class="status-bar" id="status"><span class="pulse yellow"></span> Conectando...</div>
<div class="grid">
  <div class="card ch1"><div class="card-label">Canal 1 — Test</div><div class="card-temp" id="ch1">--.-</div><span class="card-unit">°C</span></div>
  <div class="card ch2"><div class="card-label">Canal 2 — Test</div><div class="card-temp" id="ch2">--.-</div><span class="card-unit">°C</span></div>
  <div class="card ch3"><div class="card-label">Canal 3 — Sales</div><div class="card-temp" id="ch3">--.-</div><span class="card-unit">°C</span></div>
  <div class="card ch4"><div class="card-label">Canal 4 — Cámaras</div><div class="card-temp" id="ch4">--.-</div><span class="card-unit">°C</span></div>
</div>
<div class="timestamp" id="timestamp">Esperando datos...</div>
<div class="chart-container">
  <div class="chart-card">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px">
      <h2 style="margin:0">📈 Temperatura — Sales vs Cámaras</h2>
      <div id="span-selector" style="display:flex;gap:4px;flex-wrap:wrap">
        <button onclick="setSpan(60)" data-m="60" class="span-btn active">1h</button>
        <button onclick="setSpan(120)" data-m="120" class="span-btn">2h</button>
        <button onclick="setSpan(240)" data-m="240" class="span-btn">4h</button>
        <button onclick="setSpan(480)" data-m="480" class="span-btn">8h</button>
        <button onclick="setSpan(720)" data-m="720" class="span-btn">12h</button>
        <button onclick="setSpan(1440)" data-m="1440" class="span-btn">24h</button>
      </div>
    </div>
    <div style="position:relative;height:380px"><canvas id="chart"></canvas></div>
    <div id="chart-stats" style="text-align:center;padding:10px 0 0;font-family:'JetBrains Mono',monospace;font-size:12px;color:#64748b">Cargando datos...</div>
  </div>
</div>
<style>
.span-btn{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);color:#94a3b8;padding:6px 14px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;transition:all .2s;font-family:'JetBrains Mono',monospace}
.span-btn:hover{background:rgba(34,211,238,.1);border-color:rgba(34,211,238,.3);color:#e2e8f0}
.span-btn.active{background:rgba(34,211,238,.2);border-color:#22d3ee;color:#22d3ee;box-shadow:0 0 12px rgba(34,211,238,.15)}
</style>
<script>
const ctx=document.getElementById('chart').getContext('2d');
let currentSpan=60; // minutes — default 1h

// Band plugin — subtle background tint for each axis zone
const bandPlugin={
  id:'tempBands',
  beforeDraw(chart){
    const {ctx:c,chartArea:{left,right}}=chart;
    if(!left) return;
    const yL=chart.scales.yLeft, yR=chart.scales.yRight;
    if(yL){
      c.fillStyle='rgba(34,211,238,.03)';
      c.fillRect(left,yL.top,right-left,yL.bottom-yL.top);
    }
    if(yR){
      // thin right-side accent line
      c.fillStyle='rgba(251,146,60,.02)';
      c.fillRect(left,yR.top,right-left,yR.bottom-yR.top);
    }
  }
};

const chart=new Chart(ctx,{type:'line',data:{labels:[],datasets:[
  {label:'Sales (CH3)',borderColor:'#38bdf8',backgroundColor:'rgba(56,189,248,.06)',data:[],tension:.3,pointRadius:2,pointBackgroundColor:'#38bdf8',borderWidth:2.5,fill:true,yAxisID:'yLeft'},
  {label:'Cámaras (CH4)',borderColor:'#fb923c',backgroundColor:'rgba(251,146,60,.06)',data:[],tension:.3,pointRadius:2,pointBackgroundColor:'#fb923c',borderWidth:2.5,fill:true,yAxisID:'yRight'}
]},plugins:[bandPlugin],options:{
  responsive:true,
  maintainAspectRatio:false,
  animation:false,
  interaction:{intersect:false,mode:'index'},
  plugins:{
    legend:{
      position:'top',
      labels:{color:'#e2e8f0',font:{family:'Inter',size:13,weight:'600'},usePointStyle:true,pointStyle:'circle',padding:16}
    },
    tooltip:{
      backgroundColor:'rgba(15,23,42,.95)',borderColor:'rgba(255,255,255,.1)',borderWidth:1,
      titleFont:{family:'JetBrains Mono',size:12},bodyFont:{family:'JetBrains Mono',size:12},padding:10,
      callbacks:{
        title:function(items){
          if(!items.length) return '';
          const raw=items[0].label||'';
          // raw is already formatted time from fmtTime. Add date from original timestamp
          try{
            const fullTs=chart._originalTimestamps?chart._originalTimestamps[items[0].dataIndex]:null;
            if(fullTs){
              const d=new Date(fullTs);
              const dd=String(d.getDate()).padStart(2,'0');
              const mm=String(d.getMonth()+1).padStart(2,'0');
              const yyyy=d.getFullYear();
              return dd+'/'+mm+'/'+yyyy+' — '+raw;
            }
          }catch(e){}
          return raw;
        },
        label:function(c){return c.dataset.label+': '+c.parsed.y.toFixed(1)+'°C'}
      }
    }
  },
  scales:{
    x:{
      title:{display:true,text:'Hora — Día',color:'#64748b',font:{size:11}},
      ticks:{color:'#64748b',maxTicksLimit:12,font:{family:'JetBrains Mono',size:10},maxRotation:0},
      grid:{color:'rgba(255,255,255,.04)'}
    },
    yLeft:{
      type:'linear',position:'left',
      title:{display:true,text:'Sales (°C)',color:'#38bdf8',font:{size:12,weight:'700'}},
      grace:'10',
      ticks:{color:'#38bdf8',stepSize:10,callback:v=>v+'°',font:{family:'JetBrains Mono',size:11,weight:'600'}},
      grid:{color:'rgba(56,189,248,.08)',lineWidth:1},
      border:{color:'rgba(56,189,248,.3)'},
      afterDataLimits(scale){const range=scale.max-scale.min;if(range<30){const mid=(scale.max+scale.min)/2;scale.min=mid-15;scale.max=mid+15}}
    },
    yRight:{
      type:'linear',position:'right',
      title:{display:true,text:'Cámaras (°C)',color:'#fb923c',font:{size:12,weight:'700'}},
      grace:'10',
      ticks:{color:'#fb923c',stepSize:10,callback:v=>v+'°',font:{family:'JetBrains Mono',size:11,weight:'600'}},
      grid:{drawOnChartArea:false},
      border:{color:'rgba(251,146,60,.3)'},
      afterDataLimits(scale){const range=scale.max-scale.min;if(range<30){const mid=(scale.max+scale.min)/2;scale.min=mid-15;scale.max=mid+15}}
    }
  }
}});

function fmtTime(ts){
  if(!ts) return '';
  if(/^[0-9]{2}:[0-9]{2}:[0-9]{2}$/.test(ts)) return ts;
  try{
    const d=new Date(ts);
    if(isNaN(d.getTime())) return ts;
    return d.toLocaleTimeString('es-ES',{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
  }catch(e){return ts}
}

function setSpan(m){
  currentSpan=m;
  document.querySelectorAll('.span-btn').forEach(b=>{
    b.classList.toggle('active',parseInt(b.dataset.m)===m);
  });
  loadChart();
}

function loadChart(){
  fetch('/api/readings/recent?minutes='+currentSpan).then(r=>r.json()).then(d=>{
    const readings=d.readings||[];
    const labels=readings.map(r=>fmtTime(r.timestamp));
    const dataSales=readings.map(r=>r.temp_sales!==null&&r.temp_sales!==undefined?Math.round(r.temp_sales*10)/10:null);
    const dataCams=readings.map(r=>r.temp_cameras!==null&&r.temp_cameras!==undefined?Math.round(r.temp_cameras*10)/10:null);

    chart.data.labels=labels;
    chart.data.datasets[0].data=dataSales;
    chart.data.datasets[1].data=dataCams;
    chart._originalTimestamps=readings.map(r=>r.timestamp||null);
    chart.update('none');

    // Stats
    const el=document.getElementById('chart-stats');
    const v3=dataSales.filter(v=>v!==null),v4=dataCams.filter(v=>v!==null);
    let html='';
    if(v3.length){
      const last=v3[v3.length-1].toFixed(1),min=Math.min(...v3).toFixed(1),max=Math.max(...v3).toFixed(1);
      html+=`<span style="color:#22d3ee;font-weight:700">Sales: ${last}°C</span> <span style="color:#475569">(${min}–${max})</span>`;
    }
    if(v4.length){
      const last=v4[v4.length-1].toFixed(1),min=Math.min(...v4).toFixed(1),max=Math.max(...v4).toFixed(1);
      html+=` &nbsp;│&nbsp; <span style="color:#fb923c;font-weight:700">Cámaras: ${last}°C</span> <span style="color:#475569">(${min}–${max})</span>`;
    }
    const spanLabel=currentSpan>=60?`${currentSpan/60}h`:`${currentSpan}m`;
    html+=` &nbsp;│&nbsp; <span style="color:#475569">${readings.length} lecturas · ${spanLabel}</span>`;
    el.innerHTML=html;
  }).catch(()=>{});
}

function updateLive(){
  fetch('/api/tasi').then(r=>r.json()).then(d=>{
    ['CH1','CH2','CH3','CH4'].forEach(ch=>{
      const el=document.getElementById(ch.toLowerCase());
      if(d[ch]!==null&&d[ch]!==undefined){el.textContent=d[ch].toFixed(1);el.classList.remove('disconnected')}
      else{el.textContent='----';el.classList.add('disconnected')}
    });
    document.getElementById('timestamp').textContent=d.timestamp?'⏱ '+d.timestamp:'Sin datos';
    const st=document.getElementById('status');
    const isReading=d.status==='reading';
    st.innerHTML='<span class="pulse '+(isReading?'green':d.status==='disconnected'?'red':'yellow')+'"></span> '+(isReading?'Leyendo en vivo — TASI TA612C':d.status);
  }).catch(()=>{});
}

// Initial load + auto-refresh
loadChart();
updateLive();
setInterval(loadChart,3000);
setInterval(updateLive,2000);
</script>
</body>
</html>"""

# ─── DASHBOARD HTML ───────────────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TSC Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
:root{--bg:#0a0a0f;--surface:#12121f;--border:#1e1e32;--muted:#64748b;--accent:#22c55e;--load1:#22c55e;--load2:#3b82f6;--load3:#facc15;--load4:#ef4444}
*{margin:0;box-sizing:border-box}
body{font-family:'Segoe UI','Inter',system-ui,sans-serif;background:var(--bg);color:#e2e8f0;min-height:100vh}
.topbar{background:linear-gradient(135deg,#0f172a,#1e1b4b);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100}
.topbar h1{font-size:22px;background:linear-gradient(135deg,#22c55e,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.topbar .links{display:flex;gap:4px}
.topbar .links a{color:var(--muted);text-decoration:none;padding:6px 12px;font-size:14px;border-radius:6px;transition:all .2s}
.topbar .links a:hover{color:#e2e8f0;background:rgba(255,255,255,.05)}
.topbar .links a.active{color:var(--accent);font-weight:600}
.topbar .links .logout{color:#ef4444;margin-left:12px;border:1px solid rgba(239,68,68,.3)}
.container{max-width:1400px;margin:0 auto;padding:20px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;text-align:center}
.stat .val{font-size:28px;font-weight:700;color:var(--accent)}
.stat .label{color:var(--muted);font-size:12px;margin-top:4px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:20px}
.card h3{color:var(--muted);font-size:13px;margin-bottom:12px;font-weight:500}
.grid3{display:grid;grid-template-columns:1fr 1.2fr;gap:16px;margin-bottom:20px}
.cal-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.cal-header h3{font-size:15px;color:#fff;font-weight:600}
.cal-header button{background:none;border:1px solid var(--border);color:var(--muted);cursor:pointer;padding:4px 10px;border-radius:6px;font-size:16px}
.cal-legend{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.cal-legend span{font-size:10px;color:var(--muted);display:flex;align-items:center;gap:3px}
.cal-legend span::before{content:'';width:8px;height:8px;border-radius:50%}
.cal-legend .l1::before{background:var(--load1)}.cal-legend .l2::before{background:var(--load2)}.cal-legend .l3::before{background:var(--load3)}.cal-legend .l4::before{background:var(--load4)}
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}
.cal-head{text-align:center;font-size:11px;color:var(--muted);padding:4px}
.cal-day{text-align:center;padding:6px 2px;font-size:13px;border-radius:6px;cursor:default;min-height:40px;display:flex;flex-direction:column;align-items:center;justify-content:center}
.cal-day.empty{color:transparent}.cal-day.has-loads{background:var(--surface);border:1px solid var(--border);cursor:pointer}
.cal-day.has-loads:hover{border-color:var(--accent)}
.cal-day.selected{border-color:var(--accent)!important;box-shadow:0 0 8px rgba(34,197,94,.3)}
.dot-row{display:flex;gap:2px;margin-top:2px}
.dot{width:6px;height:6px;border-radius:50%}
.dot.c1{background:var(--load1)}.dot.c2{background:var(--load2)}.dot.c3{background:var(--load3)}.dot.c4{background:var(--load4)}
.day-detail{min-height:200px}
.day-detail h3{color:var(--accent);font-size:14px;margin-bottom:10px}
.load-block{display:flex;align-items:center;padding:10px;border-radius:10px;margin-bottom:8px;gap:10px;cursor:pointer;transition:transform .1s}
.load-block:hover{transform:translateX(4px)}
.color-bar{width:4px;height:40px;border-radius:2px}
.color-bar.c1{background:var(--load1)}.color-bar.c2{background:var(--load2)}.color-bar.c3{background:var(--load3)}.color-bar.c4{background:var(--load4)}
.load-block .info{flex:1}
.load-block .name{font-weight:600;font-size:14px}
.load-block .meta{font-size:11px;color:var(--muted)}
.load-block .dur{font-size:13px;font-weight:700;white-space:nowrap}
.badge{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600}
.badge.active{background:rgba(34,197,94,.15);color:#22c55e}
.badge.completed{background:rgba(59,130,246,.15);color:#3b82f6}
/* Load detail panel */
.load-detail-panel{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:20px;margin-bottom:20px;display:none}
.load-detail-panel.visible{display:block}
.load-detail-panel h3{color:var(--accent);font-size:16px;margin-bottom:12px}
.detail-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}
.detail-item{background:rgba(255,255,255,.03);border:1px solid var(--border);border-radius:8px;padding:10px}
.detail-item .dl{font-size:11px;color:var(--muted)}
.detail-item .dv{font-size:16px;font-weight:600;margin-top:2px}
.dv.green{color:#22c55e}.dv.blue{color:#3b82f6}.dv.yellow{color:#facc15}.dv.red{color:#ef4444}
/* Maintenance */
.maint-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:20px;margin-bottom:20px}
.maint-item{display:flex;align-items:center;gap:12px;padding:10px;border-radius:10px;margin-bottom:6px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.04)}
.maint-item.due{background:rgba(34,197,94,.08);border-color:rgba(34,197,94,.2)}
.maint-dot{width:12px;height:12px;border-radius:50%;flex-shrink:0}
.maint-name{font-size:14px;font-weight:600;flex:1}
.maint-progress{height:4px;border-radius:2px;background:rgba(255,255,255,.1);margin-top:4px;overflow:hidden;width:100%}
.maint-progress-bar{height:100%;border-radius:2px}
.maint-badge{background:rgba(34,197,94,.2);color:#22c55e;font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;margin-left:6px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;color:var(--muted);padding:8px;border-bottom:1px solid var(--border);font-weight:500}
td{padding:8px;border-bottom:1px solid rgba(255,255,255,.03)}
</style>
</head>
<body>
<div class="topbar">
  <h1>TSC — Dashboard</h1>
  <div class="links">
    <a href="/">Control</a>
    <a href="/monitor">Monitor</a>
    <a href="/dashboard" class="active">Dashboard</a>
    <a href="/db">Base de Datos</a>
    <a href="/llm">LLM</a>
    <a href="/logout" class="logout">Salir</a>
  </div>
</div>
<div class="container">




<!-- Load Detail Panel -->
<div class="load-detail-panel" id="load-detail-panel">
  <h3 id="ld-title">—</h3>
  <div class="detail-grid" id="ld-grid"></div>
</div>

<!-- Calendarios -->
<div class="grid2">
  <!-- Calendario de Cargas -->
  <div class="card">
    <div class="cal-header">
      <button onclick="changeMonth(-1)">&larr;</button>
      <h3 id="cal-title">— Calendario de Cargas</h3>
      <button onclick="changeMonth(1)">&rarr;</button>
    </div>
    <div class="cal-legend">
      <span class="l1">Carga 1</span><span class="l2">Carga 2</span>
      <span class="l3">Carga 3</span><span class="l4">Carga 4+</span>
    </div>
    <div class="cal-grid" id="cal-grid"></div>
  </div>
  <!-- Day Detail -->
  <div class="card day-detail">
    <h3 id="day-title">Selecciona un dia</h3>
    <p id="day-empty" style="color:var(--muted)">Haz click en un dia con cargas</p>
    <div id="day-loads"></div>
  </div>
</div>

<!-- Calendario de Control (Maintenance) -->
<div class="grid2">
  <div class="card">
    <div class="cal-header">
      <button onclick="changeMaintMonth(-1)">&larr;</button>
      <h3 id="maint-cal-title">🔧 Calendario de Control</h3>
      <button onclick="changeMaintMonth(1)">&rarr;</button>
    </div>
    <div class="cal-legend">
      <span style="font-size:10px;color:var(--muted);display:flex;align-items:center;gap:3px"><span style="width:8px;height:8px;border-radius:50%;background:#22c55e;display:inline-block"></span> Sales</span>
      <span style="font-size:10px;color:var(--muted);display:flex;align-items:center;gap:3px"><span style="width:8px;height:8px;border-radius:50%;background:#3b82f6;display:inline-block"></span> Desenfangar</span>
      <span style="font-size:10px;color:var(--muted);display:flex;align-items:center;gap:3px"><span style="width:8px;height:8px;border-radius:50%;background:#facc15;display:inline-block"></span> Control Tª</span>
      <span style="font-size:10px;color:var(--muted);display:flex;align-items:center;gap:3px"><span style="width:8px;height:8px;border-radius:50%;background:#a855f7;display:inline-block"></span> Probetas</span>
    </div>
    <div class="cal-grid" id="maint-cal-grid"></div>
  </div>
  <div class="card">
    <h3>Contadores de mantenimiento</h3>
    <div id="maint-items"></div>
  </div>
</div>

<!-- Consultas Gráficas de Temperatura -->
<div class="grid2">
  <div class="card">
    <div class="cal-header">
      <button onclick="changeTempMonth(-1)">&larr;</button>
      <h3 id="temp-cal-title">📊 Consultas Gráficas</h3>
      <button onclick="changeTempMonth(1)">&rarr;</button>
    </div>
    <div class="cal-grid" id="temp-cal-grid"></div>
    <div style="display:flex;gap:12px;margin-top:14px;align-items:center;justify-content:center;flex-wrap:wrap">
      <label style="font-size:12px;color:var(--muted)">Hora inicio:
        <select id="temp-hour-from" style="padding:6px 10px;border-radius:6px;border:1px solid var(--border);background:var(--card);color:var(--fg);font-size:13px">
        </select>
      </label>
      <label style="font-size:12px;color:var(--muted)">Hora fin:
        <select id="temp-hour-to" style="padding:6px 10px;border-radius:6px;border:1px solid var(--border);background:var(--card);color:var(--fg);font-size:13px">
        </select>
      </label>
      <button onclick="loadTempGraph()" style="padding:8px 18px;border-radius:8px;border:none;background:linear-gradient(135deg,#3b82f6,#2563eb);color:#fff;font-size:13px;font-weight:700;cursor:pointer;transition:transform .15s" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">📈 Generar Gráfico</button>
    </div>
    <div id="temp-selected-info" style="margin-top:10px;text-align:center;font-size:12px;color:var(--accent)"></div>
  </div>
  <div class="card">
    <h3 id="temp-graph-title">📈 Curva de Temperatura</h3>
    <canvas id="tempChart" height="220"></canvas>
    <div id="temp-snapshots" style="margin-top:12px;font-size:11px;color:var(--muted);max-height:120px;overflow-y:auto"></div>
  </div>
</div>

<!-- Events -->
<div class="card" style="margin-bottom:20px">
  <h3>Ultimos eventos</h3>
  <table><thead><tr><th>ID</th><th>Fecha</th><th>Tipo</th><th>Horno</th><th>Detalles</th></tr></thead>
  <tbody id="events-body"></tbody></table>
</div>

</div>

<script>
const COLORS=['c1','c2','c3','c4'];
const COLOR_HEX=['#22c55e','#3b82f6','#facc15','#ef4444','#a855f7','#06b6d4','#f97316','#ec4899'];
const MONTHS=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
let calYear=2026,calMonth=2,calDates={},dailyChart,curveChart,breakdownData=[];

function fmtDur(s){if(!s)return '—';const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sec=s%60;if(h>0)return h+'h '+m+'m';return m+'m '+sec+'s'}

// Stats
async function loadStats(){try{const[s,l]=await Promise.all([fetch('/api/db/stats').then(r=>r.json()),fetch('/api/db/loads').then(r=>r.json())]);document.getElementById('s-loads-today').textContent=s.loads_today;document.getElementById('s-events-today').textContent=s.events_today;document.getElementById('s-readings').textContent=s.readings.toLocaleString();document.getElementById('s-total-loads').textContent=l.length}catch(e){console.error(e)}}

// Stacked bar chart with click handler
async function loadCharts(){
  try{
    breakdownData=await fetch('/api/db/loads-breakdown?days=30').then(r=>r.json());
    const labels=breakdownData.map(d=>d.date);
    const maxLoads=Math.max(...breakdownData.map(d=>d.loads.length),1);
    const datasets=[];
    for(let slot=0;slot<maxLoads;slot++){
      datasets.push({
        label:'Carga '+(slot+1),
        data:breakdownData.map(d=>{const load=d.loads[slot];return load?+(load.duration_min/60).toFixed(2):0}),
        backgroundColor:COLOR_HEX[slot%COLOR_HEX.length],
        borderWidth:0,borderRadius:slot===maxLoads-1?{topLeft:4,topRight:4}:0
      })
    }
    const stackOpts={responsive:true,onClick:(evt,elements)=>{if(elements.length>0){const di=elements[0].datasetIndex;const idx=elements[0].index;const day=breakdownData[idx];if(day&&day.loads[di]){showLoadCurve(day.loads[di])}}},plugins:{legend:{labels:{color:'#94a3b8',font:{size:11}}},tooltip:{callbacks:{label:function(ctx){const day=breakdownData[ctx.dataIndex];const load=day.loads[ctx.datasetIndex];if(!load)return'';const ot=load.ot_number?(' - OT '+load.ot_number):'';return load.name+ot+' — '+load.duration_min+' min ('+ctx.parsed.y.toFixed(1)+'h)'}}}},scales:{x:{stacked:true,grid:{color:'#2a2a3e'},ticks:{color:'#64748b',font:{size:10}}},y:{stacked:true,grid:{color:'#2a2a3e'},ticks:{color:'#64748b',stepSize:2,callback:v=>String(v).padStart(2,'0')+'h'},min:0,max:24,title:{display:true,text:'Horas del día',color:'#94a3b8'}}}};
    if(dailyChart)dailyChart.destroy();
    dailyChart=new Chart(document.getElementById('chart-daily'),{type:'bar',data:{labels,datasets},options:stackOpts});
  }catch(e){console.error(e)}
}

// Show temperature curve for a specific load
async function showLoadCurve(load){
  const info=document.getElementById('load-curve-info');
  info.textContent='Cargando '+load.name+'...';
  try{
    const detail=await fetch('/api/db/load/'+load.id).then(r=>r.json());
    const readings=await fetch('/api/db/load/'+load.id+'/readings').then(r=>r.json());

    // Update info
    const client=detail.client_name||detail.client_id||'—';
    const ot=detail.ot_number||'—';
    info.innerHTML='<b>'+load.name+'</b> | Cliente: <b style="color:#3b82f6">'+client+'</b> | OT: <b style="color:#facc15">'+ot+'</b> | '+(detail.total_minutes?detail.total_minutes+' min':'—');

    // Detail panel
    const panel=document.getElementById('load-detail-panel');
    panel.classList.add('visible');
    document.getElementById('ld-title').textContent=load.name+' — '+(detail.furnace||'');
    const items=[
      ['Cliente',client,'blue'],['OT',ot,'yellow'],
      ['Inicio',(detail.start_time||'').slice(11,19),'green'],['Fin',(detail.end_time||'').slice(11,19)||'En curso','blue'],
      ['Duracion',detail.total_minutes?detail.total_minutes+' min':'—','green'],['Temp Media',detail.avg_temp_sales?Math.round(detail.avg_temp_sales)+'°C':'—','yellow'],
      ['Temp Max',detail.max_temp_sales?Math.round(detail.max_temp_sales)+'°C':'—','red'],['Estado',detail.status||'—','green']
    ];
    document.getElementById('ld-grid').innerHTML=items.map(([l,v,c])=>'<div class="detail-item"><div class="dl">'+l+'</div><div class="dv '+c+'">'+v+'</div></div>').join('');

    // Draw curve
    if(curveChart)curveChart.destroy();
    if(readings.length>1){
      const startTs=new Date(readings[0].timestamp).getTime();
      const labels=readings.map(r=>Math.round((new Date(r.timestamp).getTime()-startTs)/60000));
      const ds=[{label:'Sales °C',data:readings.map(r=>r.temp_sales),borderColor:'#f59e0b',backgroundColor:'rgba(245,158,11,0.1)',fill:true,tension:0.3,pointRadius:1}];
      if(readings.some(r=>r.temp_cameras))ds.push({label:'Cámaras °C',data:readings.map(r=>r.temp_cameras),borderColor:'#3b82f6',backgroundColor:'rgba(59,130,246,0.1)',fill:true,tension:0.3,pointRadius:1});
      curveChart=new Chart(document.getElementById('chart-curve'),{type:'line',data:{labels,datasets:ds},options:{responsive:true,plugins:{legend:{labels:{color:'#94a3b8'}}},scales:{x:{title:{display:true,text:'Tiempo (min)',color:'#94a3b8'},ticks:{color:'#64748b'},min:0,max:250},y:{title:{display:true,text:'Temperatura (°C)',color:'#94a3b8'},ticks:{color:'#64748b'},min:500,max:700}}}});
    }else{info.innerHTML+=' — <span style="color:var(--muted)">Sin lecturas de temperatura</span>'}
  }catch(e){info.textContent='Error: '+e.message}
}

// Calendar
function changeMonth(d){calMonth+=d;if(calMonth>11){calMonth=0;calYear++}if(calMonth<0){calMonth=11;calYear--}renderCalendar()}
async function renderCalendar(){
  document.getElementById('cal-title').textContent=MONTHS[calMonth]+' '+calYear+' — Calendario de Cargas';
  let loadsByDate={};
  try{
    const dates=await fetch('/api/db/calendar-dates?month='+(calMonth+1)+'&year='+calYear).then(r=>r.json());
    calDates={};dates.forEach(d=>{calDates[d.date]=d.load_count});
    for(const d of dates){if(d.load_count>0){const dayLoads=await fetch('/api/db/loads-by-date?date='+d.date).then(r=>r.json());loadsByDate[d.date]=dayLoads}}
  }catch(e){console.error(e)}
  const grid=document.getElementById('cal-grid');grid.innerHTML='';
  ['Lu','Ma','Mi','Ju','Vi','Sa','Do'].forEach(d=>{const el=document.createElement('div');el.className='cal-head';el.textContent=d;grid.appendChild(el)});
  const first=new Date(calYear,calMonth,1);const dow=(first.getDay()+6)%7;const daysInMonth=new Date(calYear,calMonth+1,0).getDate();
  for(let i=0;i<dow;i++){const el=document.createElement('div');el.className='cal-day empty';el.textContent='.';grid.appendChild(el)}
  for(let day=1;day<=daysInMonth;day++){
    const dateStr=calYear+'-'+String(calMonth+1).padStart(2,'0')+'-'+String(day).padStart(2,'0');
    const el=document.createElement('div');const cnt=calDates[dateStr]||0;
    el.className='cal-day'+(cnt>0?' has-loads':'');el.textContent=day;
    if(cnt>0){
      const dayLoads=loadsByDate[dateStr]||[];
      const totalDur=dayLoads.reduce((s,l)=>s+(l.total_minutes||l.duration_min||0),0);
      if(totalDur>0){
        const bar=document.createElement('div');
        bar.style.cssText='display:flex;height:6px;border-radius:3px;overflow:hidden;margin-top:2px;width:100%';
        dayLoads.forEach((l,i)=>{const pct=Math.max(((l.total_minutes||l.duration_min||0)/totalDur)*100,5);const seg=document.createElement('div');seg.style.cssText='width:'+pct+'%;background:'+COLOR_HEX[Math.min(i,COLOR_HEX.length-1)];bar.appendChild(seg)});
        el.appendChild(bar)
      }else{
        const dots=document.createElement('div');dots.className='dot-row';
        for(let i=0;i<Math.min(cnt,4);i++){const dot=document.createElement('div');dot.className='dot '+COLORS[i];dots.appendChild(dot)}
        el.appendChild(dots)
      }
      el.onclick=()=>selectDay(dateStr,el)
    }
    grid.appendChild(el)
  }
}

async function selectDay(dateStr,el){
  document.querySelectorAll('.cal-day.selected').forEach(d=>d.classList.remove('selected'));
  if(el)el.classList.add('selected');
  document.getElementById('day-title').textContent='Cargas del '+dateStr;
  document.getElementById('day-empty').style.display='none';
  const loads=await fetch('/api/db/loads-by-date?date='+dateStr).then(r=>r.json());
  const container=document.getElementById('day-loads');
  if(loads.length===0){container.innerHTML='';document.getElementById('day-empty').style.display='block';document.getElementById('day-empty').textContent='Sin cargas este dia';return}
  // Group loads by start_time (same start_time = same batch/Carga)
  const groups={};
  loads.forEach(l=>{
    const key=(l.start_time||'').slice(0,19);
    if(!groups[key])groups[key]={loads:[],start_time:l.start_time,end_time:l.end_time,furnace:l.furnace,status:l.status,total_minutes:l.total_minutes,name:l.name,id:l.id};
    groups[key].loads.push(l);
    if(l.end_time&&(!groups[key].end_time||l.end_time>groups[key].end_time))groups[key].end_time=l.end_time;
  });
  let cargaNum=0;
  container.innerHTML=Object.values(groups).map(g=>{
    cargaNum++;
    const ci=COLORS[Math.min(cargaNum-1,3)];
    const fn=(g.furnace||'').replace(/sulfur_1/g,'Sursulf_2');
    const otList=g.loads.map(l=>{
      const ot=l.ot_number||'?';
      const w=l.weight?(' '+l.weight+'kg'):'';
      const dur=l.duration_min?(' '+l.duration_min+'min'):(l.total_minutes?' '+l.total_minutes+'min':'');
      return '<span style="color:#22c55e;font-weight:600">'+ot+'</span><span style="color:#94a3b8;font-size:11px">'+w+dur+'</span>';
    }).join(', ');
    const tMin=g.loads.reduce((max,l)=>Math.max(max,l.total_minutes||0),0);
    const tLabel=tMin>0?(tMin+' min'):'';
    const allDone=g.loads.every(l=>l.status==='completed');
    const anyCancelled=g.loads.some(l=>l.status==='cancelled');
    const st=allDone?'completed':anyCancelled?'cancelled':'active';
    return '<div class="load-block" style="background:var(--surface)">'
      +'<div class="color-bar '+ci+'"></div>'
      +'<div class="info">'
      +'<div class="name">Carga '+cargaNum+' &mdash; '+otList+'</div>'
      +'<div class="meta">'+fn+' &bull; '+(g.start_time||'').slice(11,19)+' - '+((g.end_time||'').slice(11,19)||'...')+'</div>'
      +(tLabel?'<div class="meta" style="color:#f59e0b;font-weight:600">&#x23f1; '+tLabel+'</div>':'')
      +'<span class="badge '+st+'">'+st+'</span>'
      +'</div></div>'
  }).join('')
}

// Maintenance Calendar
let maintYear,maintMonth;
const MAINT_COLORS={'Análisis de Sales':'#22d3ee','Desenfangar':'#22c55e','Control de Tª':'#ef4444','Probetas':'#e2e8f0'};
function changeMaintMonth(d){maintMonth+=d;if(maintMonth>11){maintMonth=0;maintYear++}if(maintMonth<0){maintMonth=11;maintYear--}loadMaintenance()}

async function loadMaintenance(){
  try{
    const m=await fetch('/api/maintenance').then(r=>r.json());
    const totalLoads=m.total_loads;
    if(document.getElementById('maint-total-loads'))document.getElementById('maint-total-loads').textContent=totalLoads;

    // Render counters with Reset buttons (synced with Control page)
    document.getElementById('maint-items').innerHTML=m.tasks.map(t=>{
      const pct=t.every>0?Math.round((t.loads_since/t.every)*100):0;
      const tn=encodeURIComponent(t.name);
      return '<div class="maint-item'+(t.due?' due':'')+'"><div class="maint-dot" style="background:'+t.color+'"></div><div style="flex:1"><div class="maint-name">'+t.name+(t.due?' <span class="maint-badge">¡TOCA!</span>':'')+'</div>'+(t.every>0?'<div class="maint-progress"><div class="maint-progress-bar" style="width:'+pct+'%;background:'+t.color+'"></div></div><div style="font-size:11px;color:var(--muted);margin-top:3px">'+t.loads_since+'/'+t.every+' — Faltan '+t.remaining+'</div>':'')+'</div><button onclick="resetMaintTask(decodeURIComponent(this.dataset.task))" data-task="'+tn+'" title="Pone el contador a 0" style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:#f87171;padding:6px 12px;border-radius:8px;font-size:11px;font-weight:600;cursor:pointer">&#x21ba; Reset</button></div>'
    }).join('');

    // Render maintenance calendar grid
    document.getElementById('maint-cal-title').textContent='🔧 '+MONTHS[maintMonth]+' '+maintYear+' — Calendario de Control';
    const grid=document.getElementById('maint-cal-grid');grid.innerHTML='';
    ['Lu','Ma','Mi','Ju','Vi','Sa','Do'].forEach(d=>{const el=document.createElement('div');el.className='cal-head';el.textContent=d;grid.appendChild(el)});
    const first=new Date(maintYear,maintMonth,1);const dow=(first.getDay()+6)%7;const daysInMonth=new Date(maintYear,maintMonth+1,0).getDate();
    for(let i=0;i<dow;i++){const el=document.createElement('div');el.className='cal-day empty';el.textContent='.';grid.appendChild(el)}

    // Estimate loads per day (avg ~2 loads/workday)
    const today=new Date();const avgLoadsPerDay=Math.max(totalLoads>0?Math.round(totalLoads/Math.max(1,Math.round((Date.now()-new Date(maintYear,0,1).getTime())/(86400000)))):1,1);
    const schedules=m.tasks.filter(t=>t.every>0);

    for(let day=1;day<=daysInMonth;day++){
      const el=document.createElement('div');el.className='cal-day';el.textContent=day;
      const dateObj=new Date(maintYear,maintMonth,day);
      const isToday=dateObj.toDateString()===today.toDateString();
      if(isToday)el.style.cssText+='border:2px solid var(--accent);border-radius:8px;';

      // Calculate which maintenance tasks are due on this day
      // Project forward from today: how many loads will have been done by this day
      const diffDays=Math.round((dateObj-today)/(86400000));
      const projectedLoads=totalLoads+Math.max(0,diffDays)*avgLoadsPerDay;
      const dueTasks=[];
      schedules.forEach(t=>{
        if(projectedLoads>0 && projectedLoads%t.every<avgLoadsPerDay){
          dueTasks.push(t);
        }
      });

      // For today, use actual due status
      if(isToday){
        const todayDue=m.tasks.filter(t=>t.due);
        if(todayDue.length>0){
          const dots=document.createElement('div');dots.className='dot-row';dots.style.cssText='display:flex;gap:2px;margin-top:2px;justify-content:center';
          todayDue.forEach(t=>{const dot=document.createElement('div');dot.style.cssText='width:8px;height:8px;border-radius:50%;background:'+t.color;dots.appendChild(dot)});
          el.appendChild(dots);
          el.style.background='rgba(34,197,94,.08)';
        }
      }else if(dueTasks.length>0 && diffDays>0){
        const dots=document.createElement('div');dots.style.cssText='display:flex;gap:2px;margin-top:2px;justify-content:center';
        dueTasks.forEach(t=>{const dot=document.createElement('div');dot.style.cssText='width:6px;height:6px;border-radius:50%;background:'+MAINT_COLORS[t.name]||t.color;dots.appendChild(dot)});
        el.appendChild(dots);
        el.style.background='rgba(255,255,255,.02)';el.style.borderRadius='6px';
      }

      // Weekends dimmed
      if(dateObj.getDay()===0||dateObj.getDay()===6)el.style.opacity='0.4';

      // Mark last_date (reset day) with a solid filled dot
      m.tasks.forEach(t => {
        if (!t.last_date) return;
        const ld = new Date(t.last_date + 'T12:00:00');
        if (ld.getFullYear() === maintYear && ld.getMonth() === maintMonth && ld.getDate() === day) {
          const resetDots = el.querySelector('.reset-dots') || (() => {
            const d = document.createElement('div');
            d.className = 'reset-dots';
            d.style.cssText = 'display:flex;gap:2px;margin-top:2px;justify-content:center';
            el.appendChild(d);
            return d;
          })();
          const dot = document.createElement('div');
          dot.title = '↺ Reset: ' + t.name;
          dot.style.cssText = 'width:7px;height:7px;border-radius:50%;background:' + (MAINT_COLORS[t.name] || t.color) + ';box-shadow:0 0 4px ' + (MAINT_COLORS[t.name] || t.color);
          resetDots.appendChild(dot);
          el.style.outline = '1px solid rgba(255,255,255,.15)';
          el.style.borderRadius = '6px';
        }
      });

      grid.appendChild(el);
    }
  }catch(e){console.error(e)}
}

// Init maintenance calendar
{const n=new Date();maintYear=n.getFullYear();maintMonth=n.getMonth()}

// ── Temperature Graph Calendar ──────────────────────────────────────────────
let tempYear,tempMonth,tempSelectedDate=null,tempChart=null;

function changeTempMonth(d){
  tempMonth+=d;
  if(tempMonth>11){tempMonth=0;tempYear++}
  if(tempMonth<0){tempMonth=11;tempYear--}
  renderTempCal();
}

function renderTempCal(){
  document.getElementById('temp-cal-title').textContent='📊 '+MONTHS[tempMonth]+' '+tempYear+' — Consultas Gráficas';
  const grid=document.getElementById('temp-cal-grid');
  grid.innerHTML='';
  // Day headers
  ['L','M','X','J','V','S','D'].forEach(d=>{
    const hdr=document.createElement('div');hdr.className='cal-hdr';hdr.textContent=d;grid.appendChild(hdr);
  });
  const first=new Date(tempYear,tempMonth,1);
  const dow=(first.getDay()+6)%7;
  const daysInMonth=new Date(tempYear,tempMonth+1,0).getDate();
  const today=new Date();
  // Empty cells
  for(let e=0;e<dow;e++){const empty=document.createElement('div');empty.className='cal-day empty';grid.appendChild(empty)}
  // Day cells
  for(let day=1;day<=daysInMonth;day++){
    const el=document.createElement('div');
    el.className='cal-day';
    el.textContent=day;
    const dateStr=tempYear+'-'+String(tempMonth+1).padStart(2,'0')+'-'+String(day).padStart(2,'0');
    const isToday=day===today.getDate()&&tempMonth===today.getMonth()&&tempYear===today.getFullYear();
    if(isToday) el.classList.add('today');
    if(dateStr===tempSelectedDate) el.style.cssText='background:#3b82f6;color:#fff;border-radius:50%;font-weight:700';
    el.onclick=()=>{
      tempSelectedDate=dateStr;
      renderTempCal();
      document.getElementById('temp-selected-info').textContent='Seleccionado: '+dateStr;
    };
    grid.appendChild(el);
  }
}

// Populate hour selectors
function initTempHours(){
  const fromSel=document.getElementById('temp-hour-from');
  const toSel=document.getElementById('temp-hour-to');
  for(let h=0;h<24;h++){
    const label=String(h).padStart(2,'0')+':00';
    fromSel.innerHTML+='<option value="'+h+'"'+(h===8?' selected':'')+'>'+label+'</option>';
    toSel.innerHTML+='<option value="'+h+'"'+(h===14?' selected':'')+'>'+label+'</option>';
  }
}

async function loadTempGraph(){
  if(!tempSelectedDate){alert('Selecciona un día del calendario primero');return}
  const hFrom=document.getElementById('temp-hour-from').value;
  const hTo=document.getElementById('temp-hour-to').value;
  if(parseInt(hFrom)>=parseInt(hTo)){alert('La hora de inicio debe ser menor que la hora fin');return}
  try{
    const data=await fetch('/api/temperature-graph?date='+tempSelectedDate+'&from='+hFrom+'&to='+hTo).then(r=>r.json());
    const readings=data.readings||[];
    const snapshots=data.snapshots||[];

    // Parse data for chart
    const labels=readings.map(r=>{
      try{return r.timestamp.slice(11,19)}catch(e){return ''}
    });
    const tempsSales=readings.map(r=>r.temperature!==null&&r.temperature!==undefined?r.temperature:null);
    const tempsCams=readings.map(r=>r.temp_cameras!==null&&r.temp_cameras!==undefined?r.temp_cameras:null);
    const hasCams=tempsCams.some(v=>v!==null);

    // Update title
    document.getElementById('temp-graph-title').textContent='📈 '+tempSelectedDate+' ('+String(hFrom).padStart(2,'0')+':00 - '+String(hTo).padStart(2,'0')+':00)';

    // Render chart
    if(tempChart) tempChart.destroy();
    const ctx=document.getElementById('tempChart').getContext('2d');
    const datasets=[{
      label:'Sales (CH3)',
      data:tempsSales,
      borderColor:'#22d3ee',
      backgroundColor:'rgba(34,211,238,0.08)',
      borderWidth:2.5,
      pointRadius:0,
      fill:true,
      tension:0.3,
      yAxisID:'yLeft'
    }];
    if(hasCams){
      datasets.push({
        label:'Cámaras (CH4)',
        data:tempsCams,
        borderColor:'#fb923c',
        backgroundColor:'rgba(251,146,60,0.06)',
        borderWidth:2.5,
        pointRadius:0,
        fill:true,
        tension:0.3,
        yAxisID:'yRight'
      });
    }
    tempChart=new Chart(ctx,{
      type:'line',
      data:{labels:labels,datasets:datasets},
      options:{
        responsive:true,
        animation:false,
        interaction:{intersect:false,mode:'index'},
        plugins:{
          legend:{labels:{color:'#94a3b8',font:{size:11},usePointStyle:true}},
          tooltip:{
            mode:'index',intersect:false,
            backgroundColor:'rgba(15,23,42,.95)',
            borderColor:'rgba(255,255,255,.1)',borderWidth:1,
            titleFont:{family:'JetBrains Mono',size:11},
            bodyFont:{family:'JetBrains Mono',size:11},padding:8
          }
        },
        scales:{
          x:{grid:{color:'#2a2a3e'},ticks:{color:'#64748b',font:{size:9},maxTicksLimit:12},
             title:{display:true,text:'Hora — Día',color:'#64748b',font:{size:10}}},
          yLeft:{
            type:'linear',position:'left',
            grid:{color:'rgba(34,211,238,.08)'},
            border:{color:'rgba(34,211,238,.3)'},
            title:{display:true,text:'Sales (°C)',color:'#22d3ee',font:{size:11,weight:'700'}},
            ticks:{color:'#22d3ee',callback:v=>v+'°',font:{family:'JetBrains Mono',size:10}}
          },
          yRight:{
            type:'linear',position:'right',
            grid:{drawOnChartArea:false},
            border:{color:'rgba(251,146,60,.3)'},
            title:{display:hasCams,text:'Cámaras (°C)',color:'#fb923c',font:{size:11,weight:'700'}},
            ticks:{color:'#fb923c',callback:v=>v+'°',font:{family:'JetBrains Mono',size:10}},
            display:hasCams
          }
        }
      }
    });

    // Show snapshots below
    const snapDiv=document.getElementById('temp-snapshots');
    if(snapshots.length>0){
      snapDiv.innerHTML='<strong style="color:var(--accent)">Snapshots (cada 30 min):</strong><br>'+
        snapshots.map(s=>{
          const time=s.timestamp?s.timestamp.slice(11,19):'';
          const temp=s.temperature!==null?s.temperature.toFixed(1)+'°C':'--';
          const status=s.load_status==='active'?'🟢':'⚫';
          return status+' '+time+' — '+temp+' — OT:'+( s.ot_number||'—')+' '+( s.subload_summary||'idle');
        }).join('<br>');
    }else{
      snapDiv.innerHTML='<span style="color:#64748b">Sin snapshots para este rango. Se registran cada 30 min.</span>';
    }

    if(readings.length===0){
      snapDiv.innerHTML+='<br><span style="color:#facc15">⚠ Sin lecturas de temperatura para este día/rango.</span>';
    }
  }catch(e){console.error(e);alert('Error cargando datos: '+e.message)}
}

// Init temperature calendar
{const n=new Date();tempYear=n.getFullYear();tempMonth=n.getMonth();initTempHours();renderTempCal()}

// Events
async function loadEvents(){try{const events=await fetch('/api/db/events').then(r=>r.json());document.getElementById('events-body').innerHTML=events.slice(0,15).map(e=>'<tr><td>'+e.id+'</td><td>'+(e.timestamp||'').slice(0,19)+'</td><td><span class="badge '+(e.event_type==='LOAD_START'?'active':'completed')+'">'+e.event_type+'</span></td><td>'+(e.furnace||'')+'</td><td>'+(e.details||'')+'</td></tr>').join('')}catch(e){console.error(e)}}

// Maintenance Adjust — shared with Control page
let adjustingMaintTask=null;
function openMaintAdjust(taskName){
  adjustingMaintTask=taskName;
  const modal=document.getElementById('maint-adjust-modal');
  if(!modal){
    const m=document.createElement('div');m.id='maint-adjust-modal';
    m.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.7);z-index:9999;display:flex;align-items:center;justify-content:center';
    m.innerHTML='<div style="background:#1a1a2e;border:1px solid rgba(255,255,255,.15);border-radius:16px;padding:28px;max-width:420px;width:90%;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.5)"><div style="font-size:28px;margin-bottom:12px">📅</div><div style="font-size:16px;font-weight:700;color:#fff;margin-bottom:8px" id="maint-adj-title"></div><input type="date" id="maint-adj-date" style="padding:12px;border-radius:10px;border:1px solid rgba(255,255,255,.2);background:#0f0f23;color:#fff;font-size:15px;width:100%;box-sizing:border-box;margin-bottom:16px"><div style="display:flex;gap:12px;justify-content:center"><button onclick="submitMaintAdjust()" style="background:linear-gradient(135deg,#3b82f6,#2563eb);color:#fff;border:none;padding:12px 32px;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer">✓ OK</button><button onclick="closeMaintAdjust()" style="background:rgba(255,255,255,.08);color:#94a3b8;border:1px solid rgba(255,255,255,.15);padding:12px 32px;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer">Cancelar</button></div></div>';
    document.body.appendChild(m);
  }else{modal.style.display='flex'}
  document.getElementById('maint-adj-title').textContent='¿Cuándo fue el último control de '+taskName+'?';
  document.getElementById('maint-adj-date').value=new Date().toISOString().slice(0,10);
}
function closeMaintAdjust(){const m=document.getElementById('maint-adjust-modal');if(m)m.style.display='none';adjustingMaintTask=null}
async function submitMaintAdjust(){
  const date=document.getElementById('maint-adj-date').value;
  if(!date||!adjustingMaintTask)return;
  await fetch('/api/maintenance/adjust',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:adjustingMaintTask,last_date:date})});
  closeMaintAdjust();loadMaintenance();
}
async function resetMaintTask(taskName){
  if(!confirm('Reset "'+taskName+'"\\n\\nEl contador volvera a 0.\\n\\nConfirmar?')) return;
  await fetch('/api/maintenance/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:taskName})});
  loadMaintenance();
}

// Init
const now=new Date();calYear=now.getFullYear();calMonth=now.getMonth();
loadStats();loadCharts();loadEvents();renderCalendar();loadMaintenance();
setInterval(()=>{loadStats();loadEvents()},10000);
</script>
</body>
</html>"""

# ─── LLM DATABASE QUERY ──────────────────────────────────────────────────────
import urllib.request as _urlreq
import re as _re

def _parse_date(text):
    """Extract and convert date from text. Supports relative dates, DD/MM/YYYY, 'del día X de marzo', etc."""
    from datetime import datetime, timedelta
    now = datetime.now(MADRID_TZ)
    
    # Relative dates (check first, before month parsing could match)
    if 'anteayer' in text:
        return (now - timedelta(days=2)).strftime('%Y-%m-%d')
    if 'ayer' in text:
        return (now - timedelta(days=1)).strftime('%Y-%m-%d')
    if 'hoy' in text:
        return now.strftime('%Y-%m-%d')
    m = _re.search(r'hace\s+(\d+)\s*(?:días|dias|day)', text, _re.IGNORECASE)
    if m:
        return (now - timedelta(days=int(m.group(1)))).strftime('%Y-%m-%d')
    if 'semana pasada' in text:
        return (now - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # DD/MM/YYYY
    m = _re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    # DD/MM/YY
    m = _re.search(r'(\d{1,2})/(\d{1,2})/(\d{2})\b', text)
    if m:
        return f"20{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    # "(el|del) (día) X de MONTH (de|del) YYYY"
    MONTHS_MAP = {'enero':'01','febrero':'02','marzo':'03','abril':'04','mayo':'05','junio':'06',
                  'julio':'07','agosto':'08','septiembre':'09','octubre':'10','noviembre':'11','diciembre':'12'}
    m = _re.search(r'(?:el|del)?\s*(?:día\s+)?(\d{1,2})\s+de\s+(\w+)(?:\s+(?:de|del)\s+(\d{4}))?', text, _re.IGNORECASE)
    if m:
        day = m.group(1).zfill(2)
        month_name = m.group(2).lower()
        month = MONTHS_MAP.get(month_name)
        year = m.group(3) or '2026'
        if month:
            return f"{year}-{month}-{day}"
    # YYYY-MM-DD already
    m = _re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if m:
        return m.group(1)
    return None

def _parse_month(text):
    """Extract month from text like 'en febrero', 'en marzo'. Returns 'YYYY-MM' or None."""
    MONTHS_MAP = {'enero':'01','febrero':'02','marzo':'03','abril':'04','mayo':'05','junio':'06',
                  'julio':'07','agosto':'08','septiembre':'09','octubre':'10','noviembre':'11','diciembre':'12'}
    for month_name, month_num in MONTHS_MAP.items():
        if month_name in text.lower():
            ym = _re.search(r'(\d{4})', text)
            year = ym.group(1) if ym else '2026'
            return f"{year}-{month_num}"
    from datetime import datetime, timedelta
    now = datetime.now(MADRID_TZ)
    if 'este mes' in text.lower():
        return now.strftime('%Y-%m')
    if 'mes pasado' in text.lower():
        first = now.replace(day=1) - timedelta(days=1)
        return first.strftime('%Y-%m')
    return None

def _parse_hours(text):
    """Extract hour range from text. Returns (from_h, to_h) or None."""
    # 'de 9 a 14', 'de 9h a 14h', 'de 09:00 a 14:00', 'entre las 9 y las 14'
    m = _re.search(r'de\s+(\d{1,2})(?::?\d{0,2})?\s*h?(?:rs|oras)?\s*a\s*(\d{1,2})(?::?\d{0,2})?\s*h?(?:rs|oras)?', text, _re.IGNORECASE)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = _re.search(r'entre\s+(?:las\s+)?(\d{1,2})\s*(?:y|-)\s*(?:las\s+)?(\d{1,2})', text, _re.IGNORECASE)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None

def _generate_sql_local(question):
    """Generate SQL from natural language question using pattern matching.
    Returns (sql, engine_used) or (None, None) if no pattern matched."""
    q = question.lower().strip()
    date = _parse_date(q)
    hours = _parse_hours(q)
    
    # ── Synonym sets ──
    TEMP_WORDS = ['temperatura', 'temperature', 'temp ', 'temp.', 'temps', 'grados',
                  '°c', 'termica', 'térmica', 'calor', 'caliente', 'fria', 'fría']
    AVG_WORDS = ['media', 'promedio', 'average', 'avg', 'mean']
    MAX_WORDS = ['máxima', 'maxima', 'max', 'pico', 'mayor', 'highest', 'alta', 'más alta']
    MIN_WORDS = ['mínima', 'minima', 'min', 'menor', 'lowest', 'baja', 'más baja']
    EVOLUTION_WORDS = ['evolución', 'evolucion', 'lecturas', 'todas', 'listado', 'cada',
                       'detalle', 'readings', 'evolution', 'historial']
    LOAD_WORDS = ['carga', 'cargas', 'load', 'loads', 'batch', 'lote', 'lotes']
    OT_WORDS = ['ot ', 'ots', 'ot.', 'orden de trabajo', 'ordenes de trabajo',
                'órdenes de trabajo', 'numero de ot', 'número de ot', 'work order']
    COUNT_WORDS = ['cuántas', 'cuantas', 'cuántos', 'cuantos', 'número de', 'numero de',
                   'total de', 'count', 'contar', 'se hicieron', 'hubo', 'hay']
    DURATION_WORDS = ['duración', 'duracion', 'duration', 'cuánto duró', 'cuanto duro',
                      'cuánto tardó', 'cuanto tardo', 'tiempo de', 'horas de']
    EVENT_WORDS = ['evento', 'eventos', 'event', 'events', 'alarma', 'alarmas',
                   'alarm', 'alarms', 'start', 'stop', 'arranque', 'parada', 'incidencia']
    RECENT_WORDS = ['última', 'ultima', 'último', 'ultimo', 'últimas', 'ultimas',
                    'últimos', 'ultimos', 'reciente', 'recientes', 'hoy', 'last', 'recent',
                    'ahora', 'actual', 'actualmente', 'en este momento', 'marca', 'tiene',
                    'está', 'esta', 'hay ahora', 'justo ahora', 'ahora mismo']
    NOW_WORDS = ['ahora', 'actual', 'actualmente', 'en este momento', 'marca', 'ahora mismo',
                 'justo ahora', 'tiene ahora']
    
    is_temp = any(w in q for w in TEMP_WORDS)
    is_load = any(w in q for w in LOAD_WORDS)
    is_ot = any(w in q for w in OT_WORDS)
    is_event = any(w in q for w in EVENT_WORDS)
    is_duration = any(w in q for w in DURATION_WORDS)
    is_recent = any(w in q for w in RECENT_WORDS)
    is_count = any(w in q for w in COUNT_WORDS)
    is_now = any(w in q for w in NOW_WORDS)
    is_alarm = any(w in q for w in ['alarma', 'alarmas', 'alarm', 'alarms'])
    is_weight = any(w in q for w in ['peso', 'weight', 'kg', 'kilo', 'kilos', 'pesada', 'pesó'])
    month = _parse_month(q)
    
    # ── Alarm queries (from alarms table) ──
    if is_alarm:
        # Alarm by reason/type pattern
        reason_match = _re.search(r'(?:por|tipo|de)\s+(.+?)(?:\?|$)', q)
        if reason_match and not date and not month:
            reason = reason_match.group(1).strip()
            sql = (f"SELECT id, timestamp, alarm_type, furnace, details, resolved "
                   f"FROM alarms WHERE details LIKE '%{reason}%' OR alarm_type LIKE '%{reason}%' "
                   f"ORDER BY timestamp DESC LIMIT 50;")
            return sql, 'local'
        if is_count and month:
            sql = (f"SELECT COUNT(*) AS total_alarmas FROM alarms "
                   f"WHERE strftime('%Y-%m', timestamp) = '{month}';")
            return sql, 'local'
        if is_count and date:
            sql = (f"SELECT COUNT(*) AS total_alarmas FROM alarms "
                   f"WHERE date(timestamp) = '{date}';")
            return sql, 'local'
        if month:
            sql = (f"SELECT id, timestamp, alarm_type, furnace, details, resolved "
                   f"FROM alarms WHERE strftime('%Y-%m', timestamp) = '{month}' "
                   f"ORDER BY timestamp LIMIT 50;")
            return sql, 'local'
        if date:
            sql = (f"SELECT id, timestamp, alarm_type, furnace, details, resolved "
                   f"FROM alarms WHERE date(timestamp) = '{date}' "
                   f"ORDER BY timestamp LIMIT 50;")
            return sql, 'local'
        # Recent alarms
        sql = ("SELECT id, timestamp, alarm_type, furnace, details, resolved "
               "FROM alarms ORDER BY timestamp DESC LIMIT 20;")
        return sql, 'local'
    
    # ── Weight queries ──
    if is_weight:
        if any(w in q for w in MAX_WORDS) and date:
            sql = (f"SELECT name, ot_number, weight, duration_min, date "
                   f"FROM loads WHERE date = '{date}' AND weight IS NOT NULL "
                   f"ORDER BY CAST(weight AS REAL) DESC LIMIT 1;")
            return sql, 'local'
        if any(w in q for w in MAX_WORDS) and month:
            sql = (f"SELECT name, ot_number, weight, duration_min, date "
                   f"FROM loads WHERE strftime('%Y-%m', date) = '{month}' AND weight IS NOT NULL "
                   f"ORDER BY CAST(weight AS REAL) DESC LIMIT 1;")
            return sql, 'local'
        if date:
            sql = (f"SELECT name, ot_number, weight, duration_min "
                   f"FROM loads WHERE date = '{date}' AND weight IS NOT NULL "
                   f"ORDER BY start_time;")
            return sql, 'local'
    
    # ── OT pattern matching (e.g. "OT que acaban en 321") ──
    if is_ot:
        # Pattern: "acab(an|en) en NNN" or "terminan en NNN"
        m_pattern = _re.search(r'(?:acab|termin)\w*\s+en\s+(\d+)', q, _re.IGNORECASE)
        if m_pattern:
            suffix = m_pattern.group(1)
            sql = (f"SELECT id, name, ot_number, furnace, date, duration_min, status "
                   f"FROM loads WHERE ot_number LIKE '%{suffix}%' "
                   f"ORDER BY date DESC, start_time DESC LIMIT 50;")
            return sql, 'local'
        # Pattern: "que contienen NNN"
        m_contains = _re.search(r'(?:contien\w*|con)\s+(\d+)', q, _re.IGNORECASE)
        if m_contains:
            val = m_contains.group(1)
            sql = (f"SELECT id, name, ot_number, furnace, date, duration_min, status "
                   f"FROM loads WHERE ot_number LIKE '%{val}%' "
                   f"ORDER BY date DESC LIMIT 50;")
            return sql, 'local'
    
    # ── Month-level count queries ──
    if is_count and month:
        if is_ot:
            sql = (f"SELECT COUNT(*) AS total_ots, COUNT(DISTINCT ot_number) AS ots_distintas "
                   f"FROM loads WHERE strftime('%Y-%m', date) = '{month}' "
                   f"AND ot_number IS NOT NULL;")
            return sql, 'local'
        if is_load:
            sql = (f"SELECT COUNT(*) AS total_cargas, "
                   f"ROUND(SUM(duration_min)/60.0, 1) AS horas_total, "
                   f"ROUND(AVG(duration_min), 0) AS media_min "
                   f"FROM loads WHERE strftime('%Y-%m', date) = '{month}';")
            return sql, 'local'
    
    # ── Month-level list queries (no count) ──
    if month and not date:
        if is_ot:
            sql = (f"SELECT id, name, ot_number, furnace, date, duration_min, status "
                   f"FROM loads WHERE strftime('%Y-%m', date) = '{month}' "
                   f"AND ot_number IS NOT NULL ORDER BY date, start_time LIMIT 50;")
            return sql, 'local'
        if is_load:
            sql = (f"SELECT id, name, furnace, date, duration_min, ot_number, status "
                   f"FROM loads WHERE strftime('%Y-%m', date) = '{month}' "
                   f"ORDER BY date, start_time LIMIT 50;")
            return sql, 'local'
    
    # ── Temperature queries ──
    if is_temp:
        # Real-time temperature query ("ahora", "actual", "marca")
        if is_now and not date:
            return '__LIVE_TEMP__', 'live'
        
        if not date and not is_recent:
            return None, None
        
        # Recent temperature (no date needed)
        if is_recent and not date:
            sql = ("SELECT timestamp, ROUND(temp_sales, 1) AS temp_sales, "
                   "ROUND(temp_cameras, 1) AS temp_cameras "
                   "FROM readings ORDER BY timestamp DESC LIMIT 20;")
            return sql, 'local'
        
        # Max temperature
        if any(w in q for w in MAX_WORDS):
            where = f"date(timestamp) = '{date}'"
            if hours:
                where = f"timestamp >= '{date} {hours[0]:02d}:00:00' AND timestamp < '{date} {hours[1]:02d}:00:00'"
            sql = (f"SELECT ROUND(MAX(temp_sales), 1) AS temp_maxima, "
                   f"timestamp FROM readings "
                   f"WHERE {where} AND temp_sales IS NOT NULL "
                   f"ORDER BY temp_sales DESC LIMIT 1;")
            return sql, 'local'
        
        # Min temperature
        if any(w in q for w in MIN_WORDS):
            where = f"date(timestamp) = '{date}'"
            if hours:
                where = f"timestamp >= '{date} {hours[0]:02d}:00:00' AND timestamp < '{date} {hours[1]:02d}:00:00'"
            sql = (f"SELECT ROUND(MIN(temp_sales), 1) AS temp_minima, "
                   f"timestamp FROM readings "
                   f"WHERE {where} AND temp_sales IS NOT NULL "
                   f"ORDER BY temp_sales ASC LIMIT 1;")
            return sql, 'local'
        
        # Evolution / detailed readings — only if explicitly asked
        if any(w in q for w in EVOLUTION_WORDS):
            if hours:
                sql = (f"SELECT timestamp, ROUND(temp_sales, 1) AS temp_sales, "
                       f"ROUND(temp_cameras, 1) AS temp_cameras "
                       f"FROM readings "
                       f"WHERE timestamp >= '{date} {hours[0]:02d}:00:00' "
                       f"AND timestamp < '{date} {hours[1]:02d}:00:00' "
                       f"ORDER BY timestamp LIMIT 50;")
            else:
                sql = (f"SELECT timestamp, ROUND(temp_sales, 1) AS temp_sales, "
                       f"ROUND(temp_cameras, 1) AS temp_cameras "
                       f"FROM readings WHERE date(timestamp) = '{date}' "
                       f"ORDER BY timestamp LIMIT 50;")
            return sql, 'local'
        
        # DEFAULT for temperature: always show average summary
        if hours:
            sql = (f"SELECT COALESCE(ROUND(AVG(temp_sales), 1), 'Sin datos') AS temperatura_media, "
                   f"COALESCE(ROUND(MIN(temp_sales), 1), 'N/A') AS temp_min, "
                   f"COALESCE(ROUND(MAX(temp_sales), 1), 'N/A') AS temp_max, "
                   f"COUNT(*) AS lecturas "
                   f"FROM readings "
                   f"WHERE (timestamp >= '{date} {hours[0]:02d}:00:00' AND timestamp < '{date} {hours[1]:02d}:00:00') "
                   f"AND temp_sales IS NOT NULL;")
        else:
            sql = (f"SELECT COALESCE(ROUND(AVG(temp_sales), 1), 'Sin datos') AS temperatura_media, "
                   f"COALESCE(ROUND(MIN(temp_sales), 1), 'N/A') AS temp_min, "
                   f"COALESCE(ROUND(MAX(temp_sales), 1), 'N/A') AS temp_max, "
                   f"COUNT(*) AS lecturas "
                   f"FROM readings "
                   f"WHERE date(timestamp) = '{date}' "
                   f"AND temp_sales IS NOT NULL;")
        return sql, 'local'
    
    # ── Load count queries ──
    if is_count and is_load:
        if date:
            sql = (f"SELECT COUNT(*) AS total_cargas FROM loads "
                   f"WHERE date = '{date}';")
            return sql, 'local'
        m = _re.search(r'(?:últimos?|ultimos?)\s+(\d+)\s*(?:días|dias|days)', q)
        if m:
            days = int(m.group(1))
            sql = (f"SELECT date, COUNT(*) AS cargas FROM loads "
                   f"WHERE date >= date('now', '-{days} days') "
                   f"GROUP BY date ORDER BY date;")
            return sql, 'local'
    
    # ── Load list/details queries ──
    if is_load and date:
        sql = (f"SELECT id, name, furnace, start_time, end_time, "
               f"duration_min, ot_number, status "
               f"FROM loads WHERE date = '{date}' "
               f"ORDER BY start_time;")
        return sql, 'local'
    
    # ── OT queries ──
    if is_ot:
        # Specific OT number lookup
        m = _re.search(r'ot\s*[#nº.]?\s*(\d+(?:/\d{2,4})?)', q, _re.IGNORECASE)
        if m:
            ot = m.group(1)
            if '/' not in ot:
                ot += '/2026'
            sql = (f"SELECT id, name, furnace, date, start_time, end_time, "
                   f"duration_min, ot_number, status "
                   f"FROM loads WHERE ot_number = '{ot}' "
                   f"ORDER BY start_time;")
            return sql, 'local'
        # OTs on a date
        if date:
            sql = (f"SELECT ot_number, name, furnace, start_time, end_time, "
                   f"duration_min, status "
                   f"FROM loads WHERE date = '{date}' "
                   f"AND ot_number IS NOT NULL "
                   f"ORDER BY start_time;")
            return sql, 'local'
    
    # ── Duration queries ──
    if is_duration and date:
        sql = (f"SELECT name, furnace, ot_number, "
               f"ROUND(duration_min, 0) AS minutos, "
               f"ROUND(total_minutes / 60.0, 1) AS horas, status "
               f"FROM loads WHERE date = '{date}' "
               f"ORDER BY start_time;")
        return sql, 'local'
    
    # ── Events queries ──
    if is_event:
        if date:
            sql = (f"SELECT id, timestamp, event_type, furnace, details "
                   f"FROM events WHERE date(timestamp) = '{date}' "
                   f"ORDER BY timestamp LIMIT 50;")
            return sql, 'local'
        sql = ("SELECT id, timestamp, event_type, furnace, details "
               "FROM events ORDER BY timestamp DESC LIMIT 30;")
        return sql, 'local'
    
    # ── Recent / last N queries ──
    if is_recent:
        # Extract "last N" number
        m = _re.search(r'(?:últimas?|ultimas?|últimos?|ultimos?|last)\s+(\d+)', q)
        n = int(m.group(1)) if m else 10
        n = min(n, 50)
        
        if is_load or any(w in q for w in LOAD_WORDS):
            sql = (f"SELECT id, name, furnace, date, start_time, end_time, "
                   f"duration_min, ot_number, status "
                   f"FROM loads ORDER BY start_time DESC LIMIT {n};")
            return sql, 'local'
        # Default recent = recent loads
        sql = (f"SELECT id, name, furnace, date, start_time, end_time, "
               f"duration_min, ot_number, status "
               f"FROM loads ORDER BY start_time DESC LIMIT {n};")
        return sql, 'local'
    
    # ── Generic date query (show everything for that date) ──
    if date:
        sql = (f"SELECT id, name, furnace, start_time, end_time, "
               f"duration_min, ot_number, status "
               f"FROM loads WHERE date = '{date}' "
               f"ORDER BY start_time;")
        return sql, 'local'
    
    # ── Live system status queries ("como va", "estado", "que pasa") ──
    STATUS_WORDS = ['estado', 'como va', 'cómo va', 'que pasa', 'qué pasa',
                    'funcionando', 'encendido', 'apagado', 'que hay', 'qué hay',
                    'hay carga', 'carga activa', 'activo', 'activa']
    if any(w in q for w in STATUS_WORDS):
        return '__LIVE_STATUS__', 'live'
    
    # ── Maintenance queries ──
    MAINT_WORDS = ['mantenimiento', 'control', 'desenfangar', 'probeta', 'análisis de sales',
                   'analisis de sales', 'calendario', 'cuándo toca', 'cuando toca',
                   'próximo control', 'proximo control']
    if any(w in q for w in MAINT_WORDS):
        return '__LIVE_MAINTENANCE__', 'live'
    
    # ── Process knowledge (ARCOR, SURSULF, OXYNIT, galvanizado, etc.) ──
    PROCESS_WORDS = ['arcor', 'sursulf', 'oxynit', 'energón', 'energon', 'nitrocarburación', 'nitrocarburacion',
                     'proceso', 'clin', 'tenifer', 'tufftride', 'melonite',
                     'capa de combinación', 'capa de combinacion', 'epsilon',
                     'azufre', 'difusión', 'difusion', 'nitruro', 'dureza',
                     'tratamiento', 'corrosión', 'corrosion', 'desgaste', 'fricción',
                     'friccion', 'gripado', 'fatiga', 'cementación', 'cementacion',
                     'cromado', 'niquelado', 'nitruración', 'nitruracion',
                     'galvanizado', 'galvanizacion', 'zinc', 'fosfatado', 'fosfato',
                     'pavonado', 'anodizado', 'pasivación', 'pasivacion', 'qpq',
                     'baño químico', 'baño quimico', 'baños', 'recubrimiento',
                     'electrolítico', 'electrolitico', 'electrodeposición',
                     'decapado', 'desengrase', 'inmersión', 'inmersion',
                     'temple', 'revenido', 'recocido', 'normalizado',
                     'carbonitruración', 'carbonitruracion', 'cianuración', 'cianuracion']
    if any(w in q for w in PROCESS_WORDS):
        return '__KNOWLEDGE_PROCESS__', 'knowledge'
    
    # ── Traceability / normative knowledge ──
    TRACE_WORDS = ['trazabilidad', 'normativa', 'norma', 'iso', 'iatf', 'nadcap',
                   'auditoría', 'auditoria', 'certificación', 'certificacion',
                   'inmutabilidad', 'inmutable', 'audit', 'cumplimiento',
                   'cqi-9', 'cqi9', 'ams ', 'din ', 'astm']
    if any(w in q for w in TRACE_WORDS):
        return '__KNOWLEDGE_TRACEABILITY__', 'knowledge'
    
    # ── Architecture knowledge ──
    ARCH_WORDS = ['arquitectura', 'sistema', 'dual-write', 'dual write', 'sqlite',
                  'supabase', 'postgresql', 'modbus', 'tasi', 'sensor', 'minipc',
                  'tailscale', 'funnel', 'flask', 'dashboard', 'monitor']
    if any(w in q for w in ARCH_WORDS):
        return '__KNOWLEDGE_ARCHITECTURE__', 'knowledge'
    
    return None, None


def _try_ollama(question):
    """Try to generate SQL via Ollama. Returns sql string or None on failure."""
    DB_SCHEMA_PROMPT = """You are a SQL expert. Given a user question about a furnace monitoring database, generate a SQLite query.

Tables:
- loads(id, name, furnace, date, start_time, end_time, total_minutes, client_id, pieces_id, status, ot_number, duration_min)
- readings(id, timestamp, furnace, slave_id, temp_sales, temp_cameras, set_point, raw_value, status)
- events(id, timestamp, event_type, furnace, details)

Rules:
- Return ONLY the raw SQL query, no explanation, no markdown.
- Use temp_sales for temperature. Date format: 'YYYY-MM-DD'. Convert DD/MM/YYYY.
- LIMIT 50 max.
"""
    try:
        prompt = DB_SCHEMA_PROMPT + "\nQuestion: " + question + "\nSQL:"
        payload = json.dumps({
            "model": "phi3:mini",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 200}
        }).encode()
        req = _urlreq.Request("http://localhost:11434/api/generate",
                              data=payload,
                              headers={"Content-Type": "application/json"})
        resp = _urlreq.urlopen(req, timeout=15)
        result = json.loads(resp.read().decode())
        raw = result.get("response", "").strip()
        # Extract SQL
        sql = raw
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0].strip()
        lines = sql.split("\n")
        sql_lines = [l for l in lines if l.strip().upper().startswith(
            ("SELECT","WITH","FROM","WHERE","GROUP","ORDER","HAVING","LIMIT","("))
            or l.strip().startswith("  ") or "SELECT" in l.upper()]
        if sql_lines:
            sql = "\n".join(sql_lines)
        sql = sql.strip().rstrip(";") + ";"
        if sql.upper().lstrip().startswith("SELECT"):
            return sql
    except Exception as e:
        print(f"[LLM] Ollama failed: {e}")
    return None



@app.route("/llm")
def llm_page():
    nav_active = "llm"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TSC — Consulta IA</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    :root{{--bg:#0d0d1a;--surface:#12122a;--border:rgba(255,255,255,.08);--muted:#64748b}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:#e2e8f0;min-height:100vh}}
    .header{{background:rgba(18,18,42,.95);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:60px;position:sticky;top:0;z-index:100}}
    .header h1{{font-size:18px;font-weight:700;background:linear-gradient(135deg,#22c55e,#16a34a);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
    .links{{display:flex;gap:8px;align-items:center}}
    .links a{{color:var(--muted);text-decoration:none;font-size:13px;font-weight:500;padding:6px 12px;border-radius:8px;transition:all .2s}}
    .links a:hover{{color:#e2e8f0;background:rgba(255,255,255,.06)}}
    .links a.active{{color:#22c55e;font-weight:700}}
    .links a.logout{{border:1px solid rgba(239,68,68,.4);color:#ef4444;padding:6px 14px;border-radius:8px}}
    .links a.logout:hover{{background:rgba(239,68,68,.1)}}
    .container{{max-width:900px;margin:40px auto;padding:0 24px}}
    .card{{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:24px;margin-bottom:20px}}
    .card-header{{display:flex;align-items:center;gap:12px;margin-bottom:18px}}
    .card-title{{font-size:18px;font-weight:700;color:#22c55e}}
    .card-sub{{font-size:12px;color:var(--muted);margin-top:2px}}
    .input-row{{display:flex;gap:10px}}
    input[type=text]{{flex:1;padding:12px 16px;border-radius:10px;border:1px solid rgba(34,197,94,.3);background:rgba(0,0,0,.3);color:#e2e8f0;font-size:14px;outline:none}}
    input[type=text]:focus{{border-color:#22c55e}}
    button.ask{{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;border:none;padding:12px 28px;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer}}
    .chips{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}}
    .chip{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:var(--muted);padding:5px 12px;border-radius:8px;font-size:11px;cursor:pointer;transition:all .2s}}
    .chip:hover{{background:rgba(34,197,94,.1);border-color:rgba(34,197,94,.3);color:#22c55e}}
    #llm-results{{min-height:200px}}
  </style>
</head>
<body>
<div class="header">
  <h1>TSC — Consulta IA</h1>
  <div class="links">
    <a href="/">Control</a>
    <a href="/monitor">Monitor</a>
    <a href="/dashboard">Dashboard</a>
    <a href="/db">Base de Datos</a>
    <a href="/llm" class="active">LLM</a>
    <a href="/logout" class="logout">Salir</a>
  </div>
</div>
<div class="container">
  <div class="card">
    <div class="card-header">
      <span style="font-size:32px">&#129302;</span>
      <div>
        <div class="card-title">Consulta con IA</div>
        <div class="card-sub">Pregunta en lenguaje natural sobre cargas, OTs, temperaturas, mantenimiento, procesos...</div>
      </div>
    </div>
    <div class="input-row">
      <input type="text" id="llm-input" placeholder="Ej: ¿Qué temperatura marca las sales ahora?" onkeydown="if(event.key==='Enter')askLLM()">
      <button class="ask" onclick="askLLM()" id="llm-submit-btn">Preguntar</button>
    </div>
    <div class="chips">
      <span class="chip" onclick="setQ(this)">Que temperatura marca las sales ahora?</span>
      <span class="chip" onclick="setQ(this)">Como va el horno?</span>
      <span class="chip" onclick="setQ(this)">Mantenimiento</span>
      <span class="chip" onclick="setQ(this)">Que es SURSULF?</span>
      <span class="chip" onclick="setQ(this)">Trazabilidad y normativa</span>
      <span class="chip" onclick="setQ(this)">Ultimas 10 cargas</span>
      <span class="chip" onclick="setQ(this)">Arquitectura del sistema</span>
    </div>
  </div>
  <div id="llm-results"></div>
</div>
<script>
function setQ(el){{document.getElementById('llm-input').value=el.textContent;askLLM()}}
async function askLLM(){{
  const q=document.getElementById('llm-input').value.trim();
  if(!q)return;
  const btn=document.getElementById('llm-submit-btn');
  const out=document.getElementById('llm-results');
  btn.disabled=true;btn.textContent='...';
  out.innerHTML='<div style="text-align:center;padding:40px"><div style="font-size:28px;animation:pulse 1.5s ease-in-out infinite">&#128269;</div><p style="color:var(--muted);margin-top:8px">Generando consulta...</p></div><style>@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}</style>';
  try{{
    const r=await fetch('/api/db/llm-query',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{question:q}})}});
    const d=await r.json();
    if(d.error){{
      out.innerHTML='<div style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);border-radius:10px;padding:16px"><p style="color:#ef4444;font-weight:600">'+d.error+'</p>'+(d.sql?'<pre style="margin-top:8px;font-size:11px;color:var(--muted);overflow-x:auto">'+d.sql+'</pre>':'')+'</div>';
      btn.disabled=false;btn.textContent='Preguntar';return
    }}
    const eng=d.engine==='ollama'?'Ollama':'Motor local';
    let html='<div style="background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.2);border-radius:10px;padding:16px;margin-bottom:12px">';
    html+='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><div style="font-size:13px;color:#22c55e;font-weight:600">'+d.question+'</div><span style="font-size:10px;background:rgba(34,197,94,.15);color:#86efac;padding:2px 8px;border-radius:8px">'+eng+'</span></div>';
    html+='<pre style="font-size:11px;color:#94a3b8;background:rgba(0,0,0,.3);padding:10px;border-radius:8px;overflow-x:auto;margin-bottom:8px;white-space:pre-wrap">'+d.sql+'</pre>';
    html+='<div style="font-size:12px;color:var(--muted)">'+d.count+' resultado(s)</div></div>';
    if(d.results&&d.results.length>0){{
      const keys=d.columns&&d.columns.length?d.columns:Object.keys(d.results[0]);
      d.results.forEach(row=>{{
        html+='<div style="margin-top:12px;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.25);border-radius:12px;padding:16px">';
        keys.forEach(k=>{{
          const v=row[k]!==null&&row[k]!==undefined?row[k]:'—';
          html+='<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 4px;border-bottom:1px solid rgba(255,255,255,.05)">';
          html+='<span style="color:#94a3b8;font-size:13px;font-weight:500">'+k+'</span>';
          html+='<span style="color:#22c55e;font-size:14px;font-weight:700;max-width:65%;text-align:right;word-break:break-word">'+v+'</span>';
          html+='</div>';
        }});
        html+='</div>';
      }});
    }}else if(d.count===0){{
      html+='<div style="text-align:center;padding:20px;color:#94a3b8">Sin resultados para esta consulta</div>';
    }}
    out.innerHTML=html;
  }}catch(e){{out.innerHTML='<div style="padding:16px"><p style="color:#ef4444">Error de red: '+e.message+'</p></div>'}}
  btn.disabled=false;btn.textContent='Preguntar';
}}
</script>
</body>
</html>"""

@app.route("/api/db/llm-query", methods=["POST"])
@require_login
def api_llm_query():
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400
    if not DB_OK:
        return jsonify({"error": "Database not available"}), 500
    
    sql = ""
    engine = "local"
    try:
        # 0. TSC-only filter — reject non-furnace questions with humor
        q_lower = question.lower()
        TSC_KEYWORDS = ['temperatura', 'temp', 'grados', 'carga', 'cargas', 'ot ', 'ots',
                        'horno', 'furnace', 'evento', 'eventos', 'alarma', 'alarmas', 'lectura',
                        'sales', 'camaras', 'cámaras', 'duración', 'duracion', 'cliente',
                        'mantenimiento', 'trazabilidad', 'pieza', 'última', 'ultima',
                        'cuántas', 'cuantas', 'cuántos', 'cuantos', 'cuánto', 'cuanto',
                        'media', 'máxima', 'maxima', 'mínima', 'minima',
                        'día', 'dia', '/', 'hoy', 'ayer', 'anteayer', 'semana',
                        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
                        'ahora', 'actual', 'marca', 'estado', 'set point', 'setpoint',
                        'activa', 'activo', 'funcionando', 'encendido', 'apagado',
                        'carga activa', 'que hay', 'como va', 'cómo va', 'qué pasa',
                        'que pasa', 'monitor', 'dashboard', 'control',
                        'peso', 'weight', 'kg', 'kilo', 'incongruencia', 'acaban', 'terminan',
                         # Knowledge base
                         'arquitectura', 'sistema', 'sqlite', 'supabase', 'tailscale', 'modbus',
                         'sursulf', 'sulfonitro', 'arcor', 'oxynit', 'oxynel', 'clin', 'hef',
                         'nitrocarburación', 'nitrocarburacion', 'nitruro', 'dureza',
                         'tratamiento', 'proceso', 'recubrimiento', 'galvanizado', 'cromado',
                         'pavonado', 'fosfatado', 'temple', 'revenido', 'cementacion',
                         'trazabilidad', 'normativa', 'norma', 'iso', 'iatf', 'nadcap', 'cqi',
                         'energón', 'energon', 'tenifer', 'tufftride', 'melonite',
                         'qué es', 'que es', 'explica', 'como funciona', 'quién eres', 'quien eres']
        import random as _random
        FUNNY_REPLIES = [
            "🔥 Yo solo sé de hornos, temperaturas y cargas. ¡Pregúntame algo del taller!",
            "🤷 Ni idea... Yo soy el cerebro del horno, no Google. ¡Hazme una pregunta sobre TSC!",
            "😅 Eso no entra en mi jurisdicción. Yo controlo sales y cámaras, no el mundo.",
            "🏭 Mi mundo empieza y acaba en el horno. Pregúntame por temperaturas, cargas u OTs.",
            "⚙️ Error 404: conocimiento no encontrado. Solo sé de hornos, cargas y temperaturas.",
            "🧠 Mi cerebro solo tiene neuronas térmicas. Pregunta algo del horno y brillaré.",
        ]
        # 0a. Quick system answers (hora, fecha, quién eres)
        # Only match EXACT short questions to avoid collisions with TSC queries
        q_stripped = q_lower.rstrip('?').rstrip('.').strip()
        QUICK_EXACT = {
            'qué hora es': lambda: f"🕐 Son las {datetime.now(MADRID_TZ).strftime('%H:%M:%S')} (hora Madrid)",
            'que hora es': lambda: f"🕐 Son las {datetime.now(MADRID_TZ).strftime('%H:%M:%S')} (hora Madrid)",
            'hora': lambda: f"🕐 Son las {datetime.now(MADRID_TZ).strftime('%H:%M:%S')} (hora Madrid)",
            'qué hora es en madrid': lambda: f"🕐 Son las {datetime.now(MADRID_TZ).strftime('%H:%M:%S')} (hora Madrid)",
            'que hora es en madrid': lambda: f"🕐 Son las {datetime.now(MADRID_TZ).strftime('%H:%M:%S')} (hora Madrid)",
            'qué fecha es': lambda: f"📅 Hoy es {datetime.now(MADRID_TZ).strftime('%d/%m/%Y')} ({datetime.now(MADRID_TZ).strftime('%A')})",
            'que fecha es': lambda: f"📅 Hoy es {datetime.now(MADRID_TZ).strftime('%d/%m/%Y')} ({datetime.now(MADRID_TZ).strftime('%A')})",
            'fecha': lambda: f"📅 Hoy es {datetime.now(MADRID_TZ).strftime('%d/%m/%Y')} ({datetime.now(MADRID_TZ).strftime('%A')})",
            'qué día es': lambda: f"📅 Hoy es {datetime.now(MADRID_TZ).strftime('%d/%m/%Y')} ({datetime.now(MADRID_TZ).strftime('%A')})",
            'que dia es': lambda: f"📅 Hoy es {datetime.now(MADRID_TZ).strftime('%d/%m/%Y')} ({datetime.now(MADRID_TZ).strftime('%A')})",
            'quién eres': lambda: "🤖 Soy Nexus TSC — el cerebro digital del horno de sales. Controlo temperaturas, gestiono cargas, registro alarmas y respondo preguntas sobre todo lo que pasa en el taller.",
            'quien eres': lambda: "🤖 Soy Nexus TSC — el cerebro digital del horno de sales. Controlo temperaturas, gestiono cargas, registro alarmas y respondo preguntas sobre todo lo que pasa en el taller.",
            'ayuda': lambda: "💡 Pregúntame sobre: temperaturas, cargas, alarmas, OTs, estado del horno, procesos (SURSULF, ARCOR...), mantenimiento, trazabilidad o normativa.",
            'help': lambda: "💡 Pregúntame sobre: temperaturas, cargas, alarmas, OTs, estado del horno, procesos (SURSULF, ARCOR...), mantenimiento, trazabilidad o normativa.",
        }
        if q_stripped in QUICK_EXACT:
            msg = QUICK_EXACT[q_stripped]()
            try: save_llm_search(question, sql_generated="QUICK_ANSWER", engine="quick", result_count=1)
            except: pass
            return jsonify({
                "question": question, "sql": "💬 Respuesta rápida",
                "columns": ["Respuesta"], "results": [{"Respuesta": msg}],
                "count": 1, "engine": "quick"
            })
        
        if not any(kw in q_lower for kw in TSC_KEYWORDS):
            msg = _random.choice(FUNNY_REPLIES)
            try: save_llm_search(question, error=msg)
            except: pass
            return jsonify({"error": msg}), 400
        
        # 1. Try local pattern-matching engine first (instant)
        sql, engine = _generate_sql_local(question)
        print(f"[LLM-DEBUG] Q='{question}' → sql='{sql}', engine='{engine}'")
        
        # ── LIVE DATA HANDLERS (no SQL needed) ──
        if sql == '__LIVE_TEMP__':
            with tasi_lock:
                live = dict(tasi_latest)
            f = FURNACES.get("sulfur_1", {})
            sales = live.get('CH3')
            camaras = live.get('CH4')
            sp = f.get('set_point', 570)
            ts = live.get("timestamp", "Sin datos")
            results = [{
                "Sales (CH3)": f"{sales}°C" if sales is not None else "Sin conexión",
                "Camaras (CH4)": f"{camaras}°C" if camaras is not None else "Sin conexión",
                "Set Point": f"{sp}°C",
                "Estado": live.get("status", "desconocido"),
                "Hora lectura": ts,
            }]
            columns = list(results[0].keys())
            # Build a human-readable summary
            summary = f"Sales: {sales}°C | Cámaras: {camaras}°C | SP: {sp}°C | {ts}" if sales is not None else "Sensor sin conexión"
            try: save_llm_search(question, sql_generated="LIVE_TEMP", engine="live", result_count=1)
            except: pass
            return jsonify({
                "question": question, "sql": f"📡 {summary}",
                "columns": columns, "results": results, "count": 1, "engine": "live"
            })
        
        if sql == '__LIVE_STATUS__':
            with tasi_lock:
                live = dict(tasi_latest)
            f = FURNACES.get("sulfur_1", {})
            status_map = {"idle": "⚪ Inactivo", "ok": "🟢 En marcha", "warning": "🟡 Tiempo excedido"}
            load_info = f.get("load_name", "Ninguna")
            ot_info = f.get("ot_number", "—")
            elapsed = f.get("elapsed_seconds", 0)
            target = f.get("target_seconds", 0)
            elapsed_str = f"{elapsed // 60}m {elapsed % 60}s" if elapsed else "0m"
            target_str = f"{target // 60}m" if target else "—"
            waiting = f.get("waiting_for_temp", False)
            results = [{
                "🏭 Horno": "Sursulf 2 (Energón)",
                "📊 Estado": "🟡 Esperando temperatura" if waiting else status_map.get(f.get("status", "idle"), f.get("status", "idle")),
                "🌡️ Sales": f"{live.get('CH3', '--')}°C" if live.get('CH3') is not None else "Sin conexión",
                "🌡️ Cámaras": f"{live.get('CH4', '--')}°C" if live.get('CH4') is not None else "Sin conexión",
                "🎯 Set Point": f"{f.get('set_point', 570)}°C",
                "📦 Carga activa": load_info if load_info else "Ninguna",
                "📋 OT": ot_info if ot_info else "—",
                "⏱️ Tiempo": f"{elapsed_str} / {target_str}",
                "🔌 TASI": live.get("status", "desconocido"),
            }]
            columns = list(results[0].keys())
            try: save_llm_search(question, sql_generated="LIVE_STATUS", engine="live", result_count=1)
            except: pass
            return jsonify({
                "question": question, "sql": "📡 Estado completo del sistema en vivo",
                "columns": columns, "results": results, "count": 1, "engine": "live"
            })
        
        if sql == '__LIVE_MAINTENANCE__':
            # Get maintenance data
            maint_dates = _load_maint_dates()
            results = []
            for m in MAINTENANCE_SCHEDULE:
                last_date = maint_dates.get(m["name"])
                if m["every"] > 0 and last_date:
                    loads_since = _count_load_days_since(last_date)
                    remaining = max(0, m["every"] - loads_since)
                    results.append({
                        "Tarea": m["name"],
                        "Cada (cargas)": m["every"],
                        "Desde último": loads_since,
                        "Faltan": remaining,
                        "Estado": "🔴 ¡TOCA!" if remaining <= 0 else f"🟢 {remaining} cargas",
                        "Último control": last_date or "No registrado"
                    })
                else:
                    results.append({
                        "Tarea": m["name"],
                        "Cada (cargas)": m["every"] if m["every"] > 0 else "Manual",
                        "Desde último": "—",
                        "Faltan": "—",
                        "Estado": "ℹ️ Manual" if m["every"] == 0 else "Sin dato",
                        "Último control": last_date or "No registrado"
                    })
            columns = list(results[0].keys()) if results else []
            try: save_llm_search(question, sql_generated="LIVE_MAINTENANCE", engine="live", result_count=len(results))
            except: pass
            return jsonify({
                "question": question, "sql": "📅 Calendario de mantenimiento en vivo",
                "columns": columns, "results": results, "count": len(results), "engine": "live"
            })
        
        # ── KNOWLEDGE BASE HANDLERS ──
        if sql == '__KNOWLEDGE_PROCESS__':
            q_lower = question.lower()
            if 'oxynit' in q_lower:
                results = [{"Proceso": "OXYNIT", "Tipo": "Oxidación controlada",
                    "Temperatura": "350-400°C", "Objetivo": "Mejorar resistencia a la corrosión",
                    "Normas": "ISO 11408, AMS 2753",
                    "Descripción": "Segunda etapa del proceso ARCOR. Genera capa de óxido Fe₃O₄ controlada sobre la capa de compuestos SURSULF. Mejora hasta 10x la resistencia a corrosión en niebla salina."}]
            elif 'arcor' in q_lower or 'clin' in q_lower:
                results = [{"Proceso": "ARCOR (CLIN)", "Tipo": "Nitrocarburación ferrítica líquida controlada",
                    "Etapas": "1) SURSULF (570°C, 90-180min) + 2) OXYNIT (350-400°C)",
                    "Dureza capa": "800-1500 HV", "Espesor": "10-25 μm capa compuestos + 0.1-0.6 mm difusión",
                    "Equivalentes": "TENIFER, TUFFTRIDE, MELONITE, QPQ, NUTRIDE",
                    "Normas": "ISO 4885:2018, ISO 20431:2023, AMS 2753, DIN 17022-4, DIN 50190-3",
                    "Ventajas": "Sin deformación, sin fragilización H₂, anticorrosión, antifricción, antidesgaste, sin Cr6+"}]
            elif 'sursulf' in q_lower or 'sulfonitro' in q_lower or 'energón' in q_lower or 'energon' in q_lower:
                results = [
                    {"Campo": "¿Qué es SURSULF?", "Detalle": (
                        "Tratamiento térmico de nitrocarburación líquida en baño de sales, activado con azufre y respetuoso con el "
                        "medio ambiente. Se aplica a piezas de acero y fundición a ~570°C ± 5°C. Aumenta la resistencia al "
                        "desgaste, fatiga y gripaje, creando una capa de compuestos de nitruros de hierro ε (epsilon) de gran dureza."
                    )},
                    {"Campo": "Temperatura de proceso", "Detalle": "570 ± 5°C — zona ferrítica, por debajo de la austenita. Sin deformación significativa de la pieza"},
                    {"Campo": "Capa de combinación ε (epsilon)", "Detalle": "Nitruros de hierro Fe₂₋₃N: espesor 10-25 μm. Muy dura, compacta, autolubricante. Gran resistencia al gripaje"},
                    {"Campo": "Zona de difusión", "Detalle": "N + C + S difunden 0.1-0.6 mm bajo la capa ε. Genera compresión residual → mejora fatiga"},
                    {"Campo": "Dureza superficial", "Detalle": "800-1500 HV según material base. Acero al C: ~800 HV · Aceros aleados: hasta 1500 HV"},
                    {"Campo": "Ventajas clave", "Detalle": "① Antidesgaste ② Antifatiga ③ Antigripado ④ Mínima deformación ⑤ Sin Cr6+ ⑥ Respetuoso con el medio ambiente ⑦ Mayor vida útil de la pieza"},
                    {"Campo": "Aplicaciones — Automoción", "Detalle": "Cigüeñales, árboles de levas, balancines, válvulas, camisas de cilindro, culatas"},
                    {"Campo": "Aplicaciones — Herramientas y maquinaria", "Detalle": "Moldes para inyección de plástico/metal/caucho, maquinaria obras públicas, equipos hidráulicos, estampas de forja"},
                    {"Campo": "Aplicaciones — Piezas funcionales", "Detalle": "Engranajes, pernos, ejes, componentes que requieran alta resistencia superficial y bajo coeficiente de fricción"},
                    {"Campo": "OXYNEL / OXYNIT (post-tratamiento)", "Detalle": "Oxidación controlada a 350-400°C tras el SURSULF → capa Fe₃O₄ → mejora resistencia a la corrosión 10-50x en niebla salina"},
                    {"Campo": "Sinónimos y procesos relacionados", "Detalle": "TENIFER (Degussa/Nitrex), ARCOR (CLIN / HEF Spain), TUFFTRIDE, MELONITE, QPQ, NUTRIDE, ISONITE — misma familia FNC"},
                    {"Campo": "Tecnología CLIN / HEF Spain", "Detalle": "SURSULF es una tecnología del grupo HEF (CLIN). HEF Spain es referente europeo en tratamientos de nitrocarburación líquida"},
                    {"Campo": "Normas aplicables", "Detalle": "ISO 4885:2018, AMS 2753 (aeroespacial), DIN 17022-4, DIN 50190-3, AIAG CQI-9"},
                    {"Campo": "Materiales compatibles", "Detalle": "Aceros al carbono, aceros aleados, fundición gris y nodular, aceros inoxidables (con mayor dificultad)"},
                    {"Campo": "TSC — Horno Sursulf 2 (Energón)", "Detalle": "Horno de sales Energón TFT. Canal CH3 = temperatura sales (proceso 570°C). Monitorizado en tiempo real en esta plataforma"},
                    {"Campo": "Energón TFT", "Detalle": "https://energontft.net/ — Fabricante español de hornos de sales para SURSULF/ARCOR. Proveedor del horno de TSC"},
                ]
                columns = ["Campo", "Detalle"]

            elif 'galvaniz' in q_lower or 'zinc' in q_lower:
                results = [
                    {"Proceso": "Galvanizado en caliente (Hot-dip)", "Temp": "450°C", "Medio": "Baño de zinc fundido",
                     "Espesor": "45-200 μm", "Normas": "ISO 1461, ISO 10684, EN 10346, ASTM A123, ASTM A153",
                     "Aplicación": "Estructuras, tornillería, perfiles, tubos. Protección catódica + barrera."},
                    {"Proceso": "Electro-galvanizado (Electrozincado)", "Temp": "20-50°C", "Medio": "Baño electrolítico ácido/alcalino",
                     "Espesor": "5-25 μm", "Normas": "ISO 2081, ISO 4042, EN 12329, ASTM B633",
                     "Aplicación": "Tornillería fina, automoción, electrodomésticos. Acabado brillante."},
                    {"Proceso": "Sherardización", "Temp": "300-500°C", "Medio": "Polvo de zinc en tambor rotatorio",
                     "Espesor": "15-75 μm", "Normas": "EN 13811, ISO 17668",
                     "Aplicación": "Piezas pequeñas, bulonería, piezas roscadas."},
                ]
            elif 'fosfat' in q_lower:
                results = [
                    {"Proceso": "Fosfatado de zinc", "Temp": "50-95°C", "Medio": "Ácido fosfórico + zinc",
                     "Espesor": "5-25 μm", "Normas": "ISO 9717, DIN 50942, MIL-DTL-16232",
                     "Aplicación": "Base para pintura, conformado en frío, protección temporal."},
                    {"Proceso": "Fosfatado de manganeso", "Temp": "85-100°C", "Medio": "Ácido fosfórico + manganeso",
                     "Espesor": "5-20 μm", "Normas": "ISO 9717, MIL-DTL-16232 Type M",
                     "Aplicación": "Retención de aceite, rodaje, antifricción. Armas, engranajes."},
                    {"Proceso": "Fosfatado de hierro", "Temp": "40-75°C", "Medio": "Ácido fosfórico",
                     "Espesor": "0.3-1 μm", "Normas": "ISO 9717",
                     "Aplicación": "Base para pintura en grandes series (automoción)."},
                ]
            elif 'pavon' in q_lower:
                results = [{"Proceso": "Pavonado (Brünierung/Blackening)", "Temp": "140°C (caliente) / 20°C (frío)",
                    "Medio": "Sales alcalinas oxidantes (NaOH + NaNO₃ + NaNO₂)",
                    "Espesor": "0.5-2.5 μm Fe₃O₄", "Color": "Negro azulado",
                    "Normas": "MIL-DTL-13924, ISO 11408, DIN 50938, AMS 2485",
                    "Aplicación": "Armas, herramientas, tornillería, piezas decorativas. Protección leve + estética."}]
            elif 'cromado' in q_lower or 'cromo' in q_lower:
                results = [
                    {"Proceso": "Cromado duro", "Temp": "50-65°C", "Medio": "CrO₃ + H₂SO₄ electrolítico",
                     "Espesor": "20-500 μm", "Dureza": "850-1000 HV",
                     "Normas": "ISO 6158, ASTM B177, AMS 2460, MIL-STD-1501",
                     "Aplicación": "Cilindros hidráulicos, moldes, ejes. ⚠️ Contiene Cr6+ (regulación REACH/RoHS)"},
                    {"Proceso": "Cromado decorativo", "Temp": "40-50°C", "Medio": "CrO₃ electrolítico sobre Ni/Cu",
                     "Espesor": "0.25-0.5 μm", "Dureza": "800+ HV",
                     "Normas": "ISO 1456, ASTM B456",
                     "Aplicación": "Automoción exterior, grifería, herrajes. ⚠️ Cr6+ en proceso."},
                ]
            elif 'niquel' in q_lower or 'níquel' in q_lower:
                results = [
                    {"Proceso": "Niquelado electrolítico", "Temp": "45-65°C", "Medio": "Watts (NiSO₄ + NiCl₂ + H₃BO₃)",
                     "Espesor": "5-50 μm", "Dureza": "150-400 HV",
                     "Normas": "ISO 1456, ISO 4526, ASTM B689",
                     "Aplicación": "Barrera anticorrosión, base cromado, decoración."},
                    {"Proceso": "Níquel químico (electroless)", "Temp": "85-95°C", "Medio": "NiSO₄ + NaH₂PO₂ (autocatalítico)",
                     "Espesor": "5-75 μm", "Dureza": "500-700 HV (tras TT)",
                     "Normas": "ISO 4527, ASTM B733, AMS 2404/2405, MIL-C-26074",
                     "Aplicación": "Uniformidad total, geometrías complejas, electrónica, petroquímica."},
                ]
            elif 'anodiz' in q_lower:
                results = [
                    {"Proceso": "Anodizado sulfúrico", "Temp": "18-22°C", "Medio": "H₂SO₄ 15-20%",
                     "Espesor": "5-25 μm", "Material": "Solo aluminio y aleaciones",
                     "Normas": "ISO 7599, MIL-A-8625 Type II, EN 12373",
                     "Aplicación": "Protección + decoración + base pintura. Coloreado posible."},
                    {"Proceso": "Anodizado duro", "Temp": "0-5°C", "Medio": "H₂SO₄ concentrado, alta densidad corriente",
                     "Espesor": "25-150 μm", "Dureza": "350-600 HV",
                     "Normas": "ISO 10074, MIL-A-8625 Type III, AMS 2469",
                     "Aplicación": "Desgaste extremo, cilindros, componentes aeroespaciales."},
                ]
            elif 'qpq' in q_lower:
                results = [{"Proceso": "QPQ (Quench-Polish-Quench)", "Temp": "580°C + 350°C",
                    "Medio": "Sales de nitrocarburación + oxidación + pulido intermedio",
                    "Espesor": "10-20 μm capa + difusión", "Rugosidad": "Ra < 0.1 μm tras pulido",
                    "Normas": "AMS 2753, ISO 4885",
                    "Aplicación": "Cilindros hidráulicos, ejes, alternativa a cromado duro SIN Cr6+. Resistencia corrosión > 500h niebla salina."}]
            elif 'temple' in q_lower or 'revenido' in q_lower or 'recocido' in q_lower:
                results = [
                    {"Proceso": "Temple (Quenching)", "Temp": "800-900°C (acero)", "Medio": "Aceite / agua / polímero / aire",
                     "Normas": "ISO 4885, ISO 683-1, ASTM A255",
                     "Descripción": "Calentamiento a austenitización + enfriamiento rápido → martensita. Dureza máxima."},
                    {"Proceso": "Revenido (Tempering)", "Temp": "150-650°C", "Medio": "Horno / baño de sales",
                     "Normas": "ISO 4885, ISO 18265",
                     "Descripción": "Tras temple. Reduce fragilidad, ajusta dureza final. Siempre necesario tras temple."},
                    {"Proceso": "Recocido (Annealing)", "Temp": "600-900°C", "Medio": "Horno, enfriamiento lento",
                     "Normas": "ISO 4885, ASTM E112",
                     "Descripción": "Ablanda el material, alivia tensiones, homogeniza microestructura."},
                ]
            elif 'cement' in q_lower or 'carbonit' in q_lower:
                results = [{"Proceso": "Cementación (Carburizing)", "Temp": "900-950°C", "Tiempo": "2-20h según profundidad",
                    "Medio": "Gas (endogas) / sales fundidas / granulado",
                    "Profundidad": "0.5-2.5 mm", "Dureza": "58-62 HRC (tras temple)",
                    "Normas": "ISO 2639, ISO 4885, ISO 6336, AMS 2759/7, AIAG CQI-9",
                    "Descripción": "Difusión de carbono en superficie. Requiere temple posterior. Deformación significativa vs ARCOR."}]
            else:
                # Generic: show catalog of all processes
                results = [
                    {"Proceso": "SURSULF", "Familia": "Nitrocarburación", "Temp": "570°C", "Normas": "ISO 4885, AMS 2753"},
                    {"Proceso": "OXYNIT", "Familia": "Oxidación", "Temp": "350-400°C", "Normas": "ISO 11408"},
                    {"Proceso": "ARCOR/CLIN", "Familia": "Nitrocarburación + Oxidación", "Temp": "570°C + 350°C", "Normas": "ISO 4885, AMS 2753"},
                    {"Proceso": "QPQ", "Familia": "Nitrocarburación + Pulido", "Temp": "580°C + 350°C", "Normas": "AMS 2753"},
                    {"Proceso": "Galvanizado caliente", "Familia": "Recubrimiento zinc", "Temp": "450°C", "Normas": "ISO 1461, EN 10346"},
                    {"Proceso": "Electrozincado", "Familia": "Electrodeposición zinc", "Temp": "20-50°C", "Normas": "ISO 2081, ASTM B633"},
                    {"Proceso": "Fosfatado Zn/Mn/Fe", "Familia": "Conversión química", "Temp": "40-100°C", "Normas": "ISO 9717"},
                    {"Proceso": "Pavonado", "Familia": "Oxidación alcalina", "Temp": "140°C", "Normas": "MIL-DTL-13924, DIN 50938"},
                    {"Proceso": "Cromado duro", "Familia": "Electrodeposición Cr", "Temp": "50-65°C", "Normas": "ISO 6158, AMS 2460"},
                    {"Proceso": "Niquelado", "Familia": "Electrodeposición Ni", "Temp": "45-65°C", "Normas": "ISO 1456, ASTM B689"},
                    {"Proceso": "Níquel químico", "Familia": "Autocatalítico Ni-P", "Temp": "85-95°C", "Normas": "ISO 4527, AMS 2404"},
                    {"Proceso": "Anodizado", "Familia": "Oxidación anódica Al", "Temp": "18-22°C", "Normas": "ISO 7599, MIL-A-8625"},
                    {"Proceso": "Cementación", "Familia": "Difusión C", "Temp": "900-950°C", "Normas": "ISO 2639, AMS 2759/7"},
                    {"Proceso": "Temple + Revenido", "Familia": "Tratamiento térmico", "Temp": "800-900°C → 150-650°C", "Normas": "ISO 4885"},
                    {"Proceso": "Pasivación", "Familia": "Conversión química", "Temp": "20-60°C", "Normas": "ASTM A967, ISO 16048"},
                ]
            columns = list(results[0].keys())
            try: save_llm_search(question, sql_generated="KNOWLEDGE_PROCESS", engine="knowledge", result_count=len(results))
            except: pass
            return jsonify({
                "question": question, "sql": "📚 Base de conocimiento — Procesos TSC",
                "columns": columns, "results": results, "count": len(results), "engine": "knowledge"
            })
        
        if sql == '__KNOWLEDGE_TRACEABILITY__':
            q_lower = question.lower()
            if 'iso' in q_lower or 'norma' in q_lower or 'normativa' in q_lower:
                results = [
                    {"Norma": "ISO 4885:2018", "Ámbito": "Vocabulario tratamiento térmico", "Aplicación": "Terminología nitruración"},
                    {"Norma": "ISO 20431:2023", "Ámbito": "Calidad tratamiento térmico", "Aplicación": "Trazabilidad y gestión calidad"},
                    {"Norma": "ISO 9001:2015", "Ámbito": "Gestión de calidad", "Aplicación": "Base de todos los sistemas"},
                    {"Norma": "IATF 16949:2016", "Ámbito": "Automoción", "Aplicación": "Obligatoria Tier 1/2/3"},
                    {"Norma": "AIAG CQI-9", "Ámbito": "Auditoría hornos", "Aplicación": "Evaluación procesos especiales"},
                    {"Norma": "AMS 2753", "Ámbito": "Aeroespacial", "Aplicación": "Nitrocarburación en sales líquidas"},
                    {"Norma": "Nadcap AC7102", "Ámbito": "Aeroespacial", "Aplicación": "Certificación tratamiento térmico"},
                ]
            else:
                results = [{
                    "Sistema": "Nexus TSC — Trazabilidad Digital",
                    "Dual-Write": "SQLite local (instantáneo) + Supabase PostgreSQL (async, cloud)",
                    "Inmutabilidad": "Triggers bloquean DELETE/UPDATE en readings, events, alarms",
                    "Audit Trail": "Tabla audit_log con usuario, timestamp, datos before/after",
                    "Datos por carga": "ID, horno, fecha, hora inicio/fin, duración, OT, cliente, pieza, proceso, temperaturas",
                    "Industrias": "Automóvil (IATF), Aeroespacial (Nadcap), Ferroviaria, Armamento, Hidráulica",
                }]
            columns = list(results[0].keys())
            try: save_llm_search(question, sql_generated="KNOWLEDGE_TRACEABILITY", engine="knowledge", result_count=len(results))
            except: pass
            return jsonify({
                "question": question, "sql": "📚 Base de conocimiento — Trazabilidad y Normativa",
                "columns": columns, "results": results, "count": len(results), "engine": "knowledge"
            })
        
        if sql == '__KNOWLEDGE_ARCHITECTURE__':
            import os as _os
            _arch_path = _os.path.join(_os.path.dirname(__file__), '..', 'ARCHITECTURE_SW.md')
            _arch_text = ""
            try:
                with open(_arch_path, 'r', encoding='utf-8') as _f:
                    _arch_text = _f.read()[:8000]  # First 8k chars
            except Exception:
                pass
            if _arch_text:
                # Return as a rich text response
                results = [{"Arquitectura del Sistema": _arch_text}]
                columns = ["Arquitectura del Sistema"]
            else:
                results = [{
                    "Componente": "MiniPC + TASI TA612C",
                    "Backend": "Flask (Python) — app.py en /home/tsc/tsc_app/",
                    "Base de datos": "SQLite (WAL mode) + Supabase PostgreSQL (dual-write async)",
                    "Sensor": "TASI TA612C — 4 canales termopar: CH3=Sales, CH4=Cámaras",
                    "Acceso remoto": "Tailscale Funnel → https://tsc.tail8dce43.ts.net/",
                    "Notificaciones": "Email via Resend API (START/STOP)",
                    "Menús": "Control (/), Monitor (/monitor), Dashboard (/dashboard), Base de Datos (/db), LLM (/db#llm)",
                    "Health check": "Cron cada 2min — reinicio automático app + Tailscale Serve",
                }]
                columns = list(results[0].keys())
            try: save_llm_search(question, sql_generated="KNOWLEDGE_ARCHITECTURE", engine="knowledge", result_count=1)
            except: pass
            return jsonify({
                "question": question, "sql": "📚 ARCHITECTURE_SW.md — Arquitectura del Sistema",
                "columns": columns, "results": results, "count": 1, "engine": "knowledge"
            })
        
        # 2. If local fails, try Ollama as fallback (with short timeout)
        if not sql:
            ollama_sql = _try_ollama(question)
            if ollama_sql:
                sql = ollama_sql
                engine = "ollama"
        
        if not sql:
            return jsonify({
                "error": "No pude entender la pregunta. Prueba a reformularla.\n"
                         "Ejemplos:\n"
                         "• '¿Qué temperatura marca las sales ahora?'\n"
                         "• '¿Cómo va el horno?' / '¿Qué estado tiene?'\n"
                         "• 'Temperatura media del 25/03/2026 de 9 a 14h'\n"
                         "• '¿Cuántas cargas el 24/03/2026?'\n"
                         "• '¿Cómo va el mantenimiento?'\n"
                         "• 'Últimas 10 cargas'"
            }), 400
        
        # Safety: only allow SELECT
        if not sql.upper().lstrip().startswith("SELECT"):
            return jsonify({"error": "Solo consultas SELECT permitidas", "sql": sql}), 400
        
        # Block dangerous keywords
        upper_sql = sql.upper()
        for kw in ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "ATTACH"]:
            if kw in upper_sql:
                return jsonify({"error": f"Keyword prohibido: {kw}", "sql": sql}), 400
        
        # Execute query
        conn = get_db()
        rows = conn.execute(sql).fetchall()
        conn.close()
        
        columns = list(rows[0].keys()) if rows else []
        results = [dict(r) for r in rows[:50]]
        
        # Log search
        try: save_llm_search(question, sql_generated=sql, engine=engine, result_count=len(results))
        except: pass
        
        return jsonify({
            "question": question,
            "sql": sql,
            "columns": columns,
            "results": results,
            "count": len(results),
            "engine": engine
        })
    except Exception as e:
        try: save_llm_search(question, sql_generated=sql, engine=engine, error=str(e))
        except: pass
        return jsonify({"error": str(e), "sql": sql}), 500

DB_VIEWER_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TSC Base de Datos</title>
<style>
:root{--bg:#0a0a0f;--surface:#12121f;--border:#1e1e32;--muted:#64748b;--accent:#22c55e}
*{margin:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:#e2e8f0;min-height:100vh}
.topbar{background:linear-gradient(135deg,#0f172a,#1e1b4b);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100}
.topbar h1{font-size:22px;background:linear-gradient(135deg,#22c55e,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.topbar .links{display:flex;gap:4px}
.topbar .links a{color:var(--muted);text-decoration:none;padding:6px 12px;font-size:14px;border-radius:6px;transition:all .2s}
.topbar .links a:hover{color:#e2e8f0;background:rgba(255,255,255,.05)}
.topbar .links a.active{color:var(--accent);font-weight:600}
.topbar .links .logout{color:#ef4444;margin-left:12px;border:1px solid rgba(239,68,68,.3)}
.container{max-width:1200px;margin:0 auto;padding:20px}
.tabs{display:flex;gap:8px;margin-bottom:16px;align-items:center}
.tabs button{background:var(--surface);border:1px solid var(--border);color:var(--muted);padding:8px 16px;border-radius:8px;cursor:pointer;font-size:13px;transition:all .2s}
.tabs button:hover{color:#e2e8f0;border-color:rgba(255,255,255,.2)}.tabs button.active{color:var(--accent);border-color:var(--accent)}
.dropdown{position:relative}
.dropdown-menu{display:none;position:absolute;top:calc(100% + 6px);left:0;background:#1a1a2e;border:1px solid var(--border);border-radius:10px;min-width:150px;z-index:200;overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,.4)}
.dropdown-menu.open{display:block}
.dropdown-menu button{display:block;width:100%;background:none;border:none;color:var(--muted);padding:10px 16px;text-align:left;font-size:13px;cursor:pointer;border-radius:0;transition:background .15s}
.dropdown-menu button:hover{background:rgba(255,255,255,.06);color:#e2e8f0}
.dropdown-menu button.active{color:var(--accent)}
.dropdown-menu .llm-item{color:#64748b;font-size:12px}
.dropdown-menu .llm-item:hover{color:#22c55e}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;color:var(--muted);padding:8px;border-bottom:1px solid var(--border);font-weight:500;position:sticky;top:60px;background:var(--bg)}
td{padding:6px 8px;border-bottom:1px solid rgba(255,255,255,.03);color:#e2e8f0}
tr:hover td{background:rgba(255,255,255,.02)}
.badge{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600}
.badge.active{background:rgba(34,197,94,.15);color:#22c55e}
.badge.completed{background:rgba(59,130,246,.15);color:#3b82f6}
</style>
</head>
<body>
<div class="topbar">
  <h1>TSC &mdash; Base de Datos</h1>
  <div class="links">
    <a href="/">Control</a>
    <a href="/monitor">Monitor</a>
    <a href="/dashboard">Dashboard</a>
    <a href="/db" class="active">Base de Datos</a>
    <a href="/llm">LLM</a>
    <a href="/logout" class="logout">Salir</a>
  </div>
</div>
<div class="container">
<div class="tabs">
  <button class="active" onclick="showTab('loads',this)">Cargas</button>
  <button onclick="showAlarms(this)">Alarmas</button>
  <!-- Oculto para el futuro:
  <button onclick="showTab('events',this)">Eventos</button>
  <div class="dropdown" id="otros-dropdown">
    <button onclick="toggleOtros(this)" id="otros-btn">Otros ▾</button>
    <div class="dropdown-menu" id="otros-menu">
      <button onclick="showTab('ots',this);closeOtros()">OTs</button>
      <button onclick="showTab('traceability',this);closeOtros()">Trazabilidad</button>
      <button onclick="showLLM(this);closeOtros()" class="llm-item">· LLM</button>
    </div>
  </div>
  -->
</div>
<div id="ot-search-bar" style="margin-bottom:16px">
  <div style="display:flex;gap:10px;align-items:center">
    <div style="position:relative;flex:1;max-width:400px">
      <input type="text" id="ot-search-input" placeholder="Buscar OT... (ej: p29)" style="width:100%;padding:10px 16px 10px 38px;border-radius:10px;border:1px solid var(--border);background:var(--surface);color:#e2e8f0;font-size:14px" onkeydown="if(event.key==='Enter')searchOT()" oninput="if(!this.value)clearSearch()">
      <span style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--muted);font-size:16px">🔍</span>
    </div>
    <button onclick="searchOT()" style="background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;border:none;padding:10px 20px;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer">Buscar</button>
  </div>
  <div id="ot-search-results" style="margin-top:12px"></div>
</div>
<div id="table-container"><p style="color:var(--muted)">Cargando...</p></div>
<div id="alarms-panel" style="display:none">
  <h3 style="color:#f87171;margin-bottom:16px">🚨 Historial de Alarmas</h3>
  <div id="alarms-table" style="overflow-x:auto"><p style="color:var(--muted)">Cargando...</p></div>
</div>
<div id="llm-panel" style="display:none">
  <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:16px">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
      <span style="font-size:24px">&#129302;</span>
      <div>
        <div style="font-size:16px;font-weight:700;color:#22c55e">Consulta con IA</div>
        <div style="font-size:11px;color:var(--muted)">Pregunta en lenguaje natural sobre cargas, OTs, temperaturas...</div>
      </div>
    </div>
    <div style="display:flex;gap:10px">
      <input type="text" id="llm-input" placeholder="Ej: Temperatura media del 24/03/2026 de 9 a 14h" style="flex:1;padding:12px 16px;border-radius:10px;border:1px solid rgba(34,197,94,.3);background:rgba(0,0,0,.3);color:#e2e8f0;font-size:14px" onkeydown="if(event.key==='Enter')askLLM()">
      <button onclick="askLLM()" id="llm-submit-btn" style="background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;border:none;padding:12px 24px;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;white-space:nowrap">Preguntar</button>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px">
      <button onclick="document.getElementById('llm-input').value=this.textContent;askLLM()" style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:var(--muted);padding:4px 10px;border-radius:6px;font-size:11px;cursor:pointer">Que temperatura marca las sales ahora?</button>
      <button onclick="document.getElementById('llm-input').value=this.textContent;askLLM()" style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:var(--muted);padding:4px 10px;border-radius:6px;font-size:11px;cursor:pointer">Como va el horno?</button>
      <button onclick="document.getElementById('llm-input').value=this.textContent;askLLM()" style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:var(--muted);padding:4px 10px;border-radius:6px;font-size:11px;cursor:pointer">Mantenimiento</button>
      <button onclick="document.getElementById('llm-input').value=this.textContent;askLLM()" style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:var(--muted);padding:4px 10px;border-radius:6px;font-size:11px;cursor:pointer">Que es SURSULF?</button>
      <button onclick="document.getElementById('llm-input').value=this.textContent;askLLM()" style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:var(--muted);padding:4px 10px;border-radius:6px;font-size:11px;cursor:pointer">Trazabilidad y normativa</button>
      <button onclick="document.getElementById('llm-input').value=this.textContent;askLLM()" style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:var(--muted);padding:4px 10px;border-radius:6px;font-size:11px;cursor:pointer">Ultimas 10 cargas</button>
      <button onclick="document.getElementById('llm-input').value=this.textContent;askLLM()" style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:var(--muted);padding:4px 10px;border-radius:6px;font-size:11px;cursor:pointer">Arquitectura del sistema</button>
    </div>
  </div>
  <div id="llm-results" style="min-height:300px"></div>
</div>
</div>
<script>
async function searchOT(){
  const q=document.getElementById('ot-search-input').value.trim();
  if(!q)return;
  const out=document.getElementById('ot-search-results');
  out.innerHTML='<p style="color:var(--muted)">Buscando...</p>';
  try{
    const data=await fetch('/api/db/search?q='+encodeURIComponent(q)).then(r=>r.json());
    if(!data.length){out.innerHTML='<p style="color:var(--muted)">Sin resultados para "'+q+'"</p>';return}
    let html='<div style="font-size:12px;color:var(--muted);margin-bottom:8px">'+data.length+' resultado(s) para "'+q+'"</div>';
    html+='<div style="display:flex;flex-direction:column;gap:8px">';
    data.forEach(r=>{
      const furnace=(r.furnace||'').replace(/sulfur_1/g,'Sursulf_2');
      const st=r.status||'';
      const badgeClass=st==='completed'?'completed':st==='active'?'active':'';
      const startT=r.start_time?new Date(r.start_time).toLocaleString('es-ES',{timeZone:'Europe/Madrid',hour:'2-digit',minute:'2-digit',second:'2-digit'}):'—';
      const endT=r.end_time?new Date(r.end_time).toLocaleString('es-ES',{timeZone:'Europe/Madrid',hour:'2-digit',minute:'2-digit',second:'2-digit'}):'—';
      const durLabel=r.total_minutes?r.total_minutes+' min':(r.duration_min?r.duration_min+' min':'—');
      html+='<div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">';
      html+='<div style="display:flex;align-items:center;gap:12px">';
      html+='<span style="font-weight:700;color:#22c55e;font-size:15px">'+(r.ot_number||'—')+'</span>';
      html+='<span style="color:var(--muted);font-size:12px">'+furnace+'</span>';
      html+='<span class="badge '+badgeClass+'">'+st+'</span>';
      html+='</div>';
      html+='<div style="display:flex;gap:16px;font-size:12px;color:#e2e8f0;flex-wrap:wrap">';
      html+='<div>📅 <b>'+(r.date||'—')+'</b></div>';
      html+='<div>⚖️ <b>'+(r.weight||'—')+' kg</b></div>';
      html+='<div>⏱️ <b>'+durLabel+'</b></div>';
      html+='<div>🕐 '+startT+' → '+endT+'</div>';
      html+='</div>';
      html+='</div>';
    });
    html+='</div>';
    out.innerHTML=html;
  }catch(e){out.innerHTML='<p style="color:#ef4444">Error: '+e.message+'</p>'}
}
function clearSearch(){document.getElementById('ot-search-results').innerHTML=''}
function showLLM(btn){
  document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('active'));
  document.getElementById('otros-btn').classList.add('active');
  btn.classList.add('active');
  document.getElementById('table-container').style.display='none';
  document.getElementById('llm-panel').style.display='block';
  document.getElementById('llm-input').focus();
}
function toggleOtros(btn){
  const menu=document.getElementById('otros-menu');
  menu.classList.toggle('open');
}
function closeOtros(){
  document.getElementById('otros-menu').classList.remove('open');
}
document.addEventListener('click',e=>{
  if(!document.getElementById('otros-dropdown').contains(e.target)) closeOtros();
});
async function showTab(tab,btn){
  document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('active'));
  if(btn)btn.classList.add('active');
  document.getElementById('table-container').style.display='block';
  document.getElementById('llm-panel').style.display='none';
  document.getElementById('alarms-panel').style.display='none';
  document.getElementById('ot-search-bar').style.display='block';
  const container=document.getElementById('table-container');
  if(tab==='alarms'){
    container.innerHTML='<div style="padding:40px;text-align:center;color:var(--muted)"><div style="font-size:48px;margin-bottom:16px">🔔</div><div style="font-size:16px;font-weight:600;color:#e2e8f0;margin-bottom:8px">Módulo de Alarmas</div><div style="font-size:13px">Las alarmas registradas aparecerán aquí.</div></div>';
    return;
  }
  try{
    const data=await fetch('/api/db/'+tab).then(r=>r.json());
    if(!data.length){container.innerHTML='<p style="color:var(--muted)">Sin datos</p>';return}
    const keys=Object.keys(data[0]);
    let html='<table><thead><tr>'+keys.map(k=>'<th>'+k+'</th>').join('')+'</tr></thead><tbody>';
    data.slice(0,200).forEach(row=>{
      html+='<tr>'+keys.map(k=>{
        let v=row[k];
        if(typeof v==='string') v=v.replace(/sulfur_1/g,'Sursulf_2');
        if(k==='status'&&v)return '<td><span class="badge '+v+'">'+v+'</span></td>';
        return '<td>'+(v!==null&&v!==undefined?v:'')+'</td>'
      }).join('')+'</tr>'
    });
    html+='</tbody></table>';
    container.innerHTML=html
  }catch(e){container.innerHTML='<p style="color:#ef4444">Error: '+e.message+'</p>'}
}
async function showAlarms(btn){
  document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('active'));
  if(btn)btn.classList.add('active');
  document.getElementById('table-container').style.display='none';
  document.getElementById('llm-panel').style.display='none';
  document.getElementById('ot-search-bar').style.display='none';
  const panel=document.getElementById('alarms-panel');
  panel.style.display='block';
  const container=document.getElementById('alarms-table');
  container.innerHTML='<p style="color:var(--muted)">Cargando alarmas...</p>';
  try{
    const data=await fetch('/api/alarm/events?limit=100').then(r=>r.json());
    if(!data.length){container.innerHTML='<p style="color:var(--muted)">No hay alarmas registradas</p>';return}
    let html='<table><thead><tr><th>ID</th><th>Tipo</th><th>Temp</th><th>Umbral</th><th>Disparada</th><th>Silenciada</th><th>Resuelta</th><th>Estado</th></tr></thead><tbody>';
    data.forEach(r=>{
      const typeLabel=r.type==='sales'?'<span style="color:#f59e0b">Sales</span>':'<span style="color:#3b82f6">C&aacute;maras</span>';
      const stClass=r.status==='active'?'color:#ef4444;font-weight:700':r.status==='silenced'?'color:#f59e0b':'color:#22c55e';
      const stIcon=r.status==='active'?'&#x1F6A8;':r.status==='silenced'?'&#x1F507;':'&#x2705;';
      html+='<tr><td>'+r.id+'</td><td>'+typeLabel+'</td><td style="color:#ef4444;font-weight:700">'+r.temperature+'&deg;C</td><td>'+r.threshold+'&deg;C</td><td>'+(r.triggered_at||'')+'</td><td>'+(r.silenced_at||'&mdash;')+'</td><td>'+(r.resolved_at||'&mdash;')+'</td><td style="'+stClass+'">'+stIcon+' '+r.status+'</td></tr>';
    });
    html+='</tbody></table>';
    container.innerHTML=html;
  }catch(e){container.innerHTML='<p style="color:#ef4444">Error: '+e.message+'</p>'}
}
async function askLLM(){
  const q=document.getElementById('llm-input').value.trim();
  if(!q)return;
  const btn=document.getElementById('llm-submit-btn');
  const out=document.getElementById('llm-results');
  btn.disabled=true;btn.textContent='...';
  out.innerHTML='<div style="text-align:center;padding:40px;min-height:200px"><div style="font-size:28px;animation:pulse 1.5s ease-in-out infinite">&#128269;</div><p style="color:var(--muted);margin-top:8px">Generando consulta...</p></div><style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}</style>';
  try{
    const r=await fetch('/api/db/llm-query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
    const d=await r.json();
    if(d.error){
      out.innerHTML='<div style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);border-radius:10px;padding:16px;min-height:100px"><p style="color:#ef4444;font-weight:600">'+d.error+'</p>'+(d.sql?'<pre style="margin-top:8px;font-size:11px;color:var(--muted);overflow-x:auto">'+d.sql+'</pre>':'')+'</div>';
      btn.disabled=false;btn.textContent='Preguntar';return
    }
    const eng=d.engine==='ollama'?'Ollama':'Motor local';
    let html='<div style="background:rgba(168,85,247,.06);border:1px solid rgba(168,85,247,.2);border-radius:10px;padding:16px;margin-bottom:12px">';
    html+='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><div style="font-size:13px;color:#22c55e;font-weight:600">'+d.question+'</div><span style="font-size:10px;background:rgba(34,197,94,.15);color:#86efac;padding:2px 8px;border-radius:8px">'+eng+'</span></div>';
    html+='<pre style="font-size:11px;color:#94a3b8;background:rgba(0,0,0,.3);padding:10px;border-radius:8px;overflow-x:auto;margin-bottom:8px;white-space:pre-wrap">'+d.sql+'</pre>';
    html+='<div style="font-size:12px;color:var(--muted)">'+d.count+' resultado(s)</div></div>';
    if(d.results&&d.results.length>0){
      const keys=d.columns&&d.columns.length?d.columns:Object.keys(d.results[0]);
      d.results.forEach(row=>{
        html+='<div style="margin-top:12px;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.25);border-radius:12px;padding:16px">';
        keys.forEach(k=>{
          const v=row[k]!==null&&row[k]!==undefined?row[k]:'—';
          html+='<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 4px;border-bottom:1px solid rgba(255,255,255,.05)">';
          html+='<span style="color:#94a3b8;font-size:13px;font-weight:500">'+k+'</span>';
          html+='<span style="color:#22c55e;font-size:16px;font-weight:700">'+v+'</span>';
          html+='</div>';
        });
        html+='</div>';
      });
    }else if(d.count===0){
      html+='<div style="text-align:center;padding:20px;color:#94a3b8">Sin resultados para esta consulta</div>';
    }
    out.innerHTML=html;
  }catch(e){out.innerHTML='<div style="padding:16px;min-height:100px"><p style="color:#ef4444">Error de red: '+e.message+'</p></div>'}
  btn.disabled=false;btn.textContent='Preguntar';
}
showTab('loads',document.querySelector('.tabs button'));
</script>
</body>
</html>"""

# ─── 30-min Temperature Snapshot Timer ────────────────────────────────────────
def _temp_snapshot_loop():
    """Background thread: record temperature snapshot every 30 minutes."""
    import time as _time
    while True:
        _time.sleep(1800)  # 30 minutes
        try:
            if DB_OK:
                # Get current temperature from TASI cache
                temp = None
                try:
                    from tasi_reader import tasi_data
                    if tasi_data and tasi_data.get("status") == "reading":
                        temp = tasi_data.get("CH3")  # Sales temperature
                except:
                    pass
                record_temperature_snapshot("sulfur_1", temp)
                print(f"[SNAPSHOT] Temperature recorded: {temp}°C")
        except Exception as e:
            print(f"[SNAPSHOT] Error: {e}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

# ─── HEALTH & STATUS ENDPOINTS (públicos, sin login) ─────────────────────────
import socket as _hsocket
import subprocess as _hsubprocess

DB_PATH_HEALTH = os.path.join(os.path.dirname(__file__), "data", "tsc.db")

def _check_tasi():
    """Estado del TASI basado en (1) status del reader thread y (2) última fila en BD"""
    try:
        status = tasi_latest.get("status", "unknown")
        connected = "connected" in status.lower()
        # Fuente de verdad: última lectura en readings (tabla activa del TASI)
        import sqlite3 as _sql
        conn = _sql.connect(DB_PATH_HEALTH, timeout=2)
        cur = conn.cursor()
        row = cur.execute("SELECT timestamp FROM readings ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        if not row or not row[0]:
            return {"ok": connected, "status": status, "last_read_seconds_ago": None}
        last = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
        now = datetime.now(MADRID_TZ)
        if last.tzinfo is None:
            last = last.replace(tzinfo=MADRID_TZ)
        age = int((now - last).total_seconds())
        # OK si: serial conectado Y última lectura <120s (margen sobre TASI_READ_INTERVAL=30s)
        ok = connected and age < 120
        return {"ok": ok, "status": status, "last_read_seconds_ago": age}
    except Exception as e:
        return {"ok": False, "status": "error", "error": str(e)}

def _check_db():
    try:
        if not os.path.exists(DB_PATH_HEALTH):
            return {"ok": False, "error": "DB file missing"}
        size_mb = round(os.path.getsize(DB_PATH_HEALTH) / 1024 / 1024, 2)
        import sqlite3 as _sql
        conn = _sql.connect(DB_PATH_HEALTH, timeout=2)
        cur = conn.cursor()
        last = cur.execute("SELECT timestamp FROM readings ORDER BY id DESC LIMIT 1").fetchone()
        total = cur.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
        conn.close()
        return {"ok": True, "size_mb": size_mb, "rows": total, "last_row_ts": last[0] if last else None}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _check_internet():
    try:
        s = _hsocket.create_connection(("1.1.1.1", 53), timeout=3)
        s.close()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _check_tailscale():
    try:
        r = _hsubprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return {"ok": False, "error": "tailscale CLI failed"}
        data = json.loads(r.stdout)
        backend = data.get("BackendState", "unknown")
        ip = data.get("Self", {}).get("TailscaleIPs", [None])[0]
        return {"ok": backend == "Running", "state": backend, "ip": ip}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.route("/health")
def health():
    """Public health endpoint — JSON for monitoring/watchdogs"""
    checks = {
        "tasi": _check_tasi(),
        "database": _check_db(),
        "internet": _check_internet(),
        "tailscale": _check_tailscale(),
    }
    all_ok = all(c.get("ok") for c in checks.values())
    response = {
        "status": "ok" if all_ok else "degraded",
        "timestamp": datetime.now(MADRID_TZ).isoformat(),
        "checks": checks,
    }
    return jsonify(response), (200 if all_ok else 503)

STATUS_HTML = """<!DOCTYPE html>
<html lang="es"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="10">
<title>TSC Estado</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,Segoe UI,system-ui,sans-serif;background:#0a0a0f;color:#fff;padding:20px;min-height:100vh}
h1{text-align:center;margin-bottom:8px;font-size:24px}
.sub{text-align:center;color:#888;margin-bottom:24px;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;max-width:900px;margin:0 auto}
.card{padding:24px;border-radius:16px;border:2px solid;text-align:center}
.card.ok{background:#0a2818;border-color:#22c55e}
.card.fail{background:#2a0a0a;border-color:#ef4444}
.icon{font-size:42px;margin-bottom:8px}
.label{font-size:18px;font-weight:600;margin-bottom:4px}
.detail{font-size:13px;color:#aaa}
.footer{text-align:center;margin-top:30px;color:#666;font-size:12px}
.global{text-align:center;padding:16px;border-radius:12px;margin:0 auto 24px;max-width:900px;font-size:18px;font-weight:600}
.global.ok{background:#0a2818;color:#22c55e;border:2px solid #22c55e}
.global.fail{background:#2a0a0a;color:#ef4444;border:2px solid #ef4444}
</style></head><body>
<h1>🏭 TSC Furnace Monitor</h1>
<div class="sub">Última actualización: {{ ts }} · Auto-refresh 10s</div>
<div class="global {{ 'ok' if all_ok else 'fail' }}">{{ '✅ TODO OK' if all_ok else '⚠️  REVISAR — Avisar a Albi' }}</div>
<div class="grid">
{% for key, label, icon, c in items %}
  <div class="card {{ 'ok' if c.ok else 'fail' }}">
    <div class="icon">{{ icon }}</div>
    <div class="label">{{ label }}</div>
    <div class="detail">{{ '✅ OK' if c.ok else '❌ FALLO' }}</div>
    <div class="detail">{{ c.detail }}</div>
  </div>
{% endfor %}
</div>
<div class="footer">tsc-app · {{ ip }} · Si algo está rojo: 1) Verificar cable de red 2) Apagar y encender MiniPC (botón 5s)</div>
</body></html>"""

@app.route("/status")
def status_page():
    """Public visual status page — for non-technical operators"""
    checks = {
        "tasi": _check_tasi(),
        "database": _check_db(),
        "internet": _check_internet(),
        "tailscale": _check_tailscale(),
    }
    all_ok = all(c.get("ok") for c in checks.values())

    def detail_tasi(c):
        if c.get("ok"): return f"Última lectura hace {c.get('last_read_seconds_ago', '?')}s"
        return c.get("status", "desconocido")[:40]

    def detail_db(c):
        if c.get("ok"): return f"{c.get('rows', 0)} lecturas · {c.get('size_mb', 0)}MB"
        return c.get("error", "error")[:40]

    def detail_net(c):
        return "Conectado" if c.get("ok") else "Sin conexión"

    def detail_ts(c):
        if c.get("ok"): return f"IP {c.get('ip', '?')}"
        return c.get("state", "desconectado")

    items = [
        ("tasi", "Horno (TASI)", "🔥", {**checks["tasi"], "detail": detail_tasi(checks["tasi"])}),
        ("database", "Base de Datos", "💾", {**checks["database"], "detail": detail_db(checks["database"])}),
        ("internet", "Internet", "🌐", {**checks["internet"], "detail": detail_net(checks["internet"])}),
        ("tailscale", "Tailscale (acceso remoto)", "🔒", {**checks["tailscale"], "detail": detail_ts(checks["tailscale"])}),
    ]
    ip = checks["tailscale"].get("ip", "?")
    return render_template_string(STATUS_HTML, items=items, all_ok=all_ok,
                                   ts=datetime.now(MADRID_TZ).strftime("%Y-%m-%d %H:%M:%S"), ip=ip)
# ─── END HEALTH & STATUS ─────────────────────────────────────────────────────


if __name__ == "__main__":
    if DB_OK:
        init_db()
    # Start 30-min snapshot thread
    snapshot_thread = threading.Thread(target=_temp_snapshot_loop, daemon=True)
    snapshot_thread.start()
    # threaded=True allows multiple concurrent users
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)),
            debug=False, threaded=True)
