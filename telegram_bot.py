#!/usr/bin/env python3
"""
TSC_Nexus_MonitorBot — Telegram interface for TSC Furnace Monitoring.

Bot: @TSC_Nexus_MonitorBot
Token env: TSC_TELEGRAM_BOT_TOKEN

Commands:
  /help         — All commands
  /temp         — Current temperatures
  /temp_history — Temperature history (last 8h)
  /loads        — Today's loads
  /load <id>    — Load detail
  /active       — Current active load
  /alarms       — Active alarms
  /status       — Full system status
  /db           — Database sync status
  /search <q>   — Natural language search
"""
import sqlite3, os, sys, asyncio, threading
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tsc.db")
BOT_TOKEN = os.environ.get("TSC_TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7024795874")

# Authorized users — add chat_ids here to give access
AUTHORIZED_CHAT_IDS = {
    7024795874,   # Alberto
}

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [TSC-BOT] %(message)s")
log = logging.getLogger("tsc_bot")


# ── Auth ──────────────────────────────────────────────────

def is_authorized(update: Update) -> bool:
    chat_id = update.effective_chat.id
    if chat_id in AUTHORIZED_CHAT_IDS:
        return True
    log.warning(f"Unauthorized access attempt from chat_id={chat_id}")
    return False


async def check_auth(update: Update) -> bool:
    if not is_authorized(update):
        await update.message.reply_text(
            "⛔ No autorizado.\n\n"
            "Envía tu chat ID al administrador para solicitar acceso.\n"
            f"Tu chat ID: `{update.effective_chat.id}`",
            parse_mode="Markdown"
        )
        return False
    return True


# ── DB helpers ────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _now_str():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d")
    except:
        return datetime.now().strftime("%Y-%m-%d")


# ── Commands ──────────────────────────────────────────────

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text(
        "🏭 *TSC Nexus Monitor Bot*\n\n"
        "📋 *Comandos disponibles:*\n\n"
        "🌡️ *Temperaturas*\n"
        "  /temp — Temperatura actual\n"
        "  /temp\\_history — Últimas 8h (resumen)\n"
        "  /tracker — Estado del Temp Tracker\n\n"
        "📦 *Cargas*\n"
        "  /loads — Cargas de hoy\n"
        "  /loads\\_week — Resumen semanal\n"
        "  /load <id> — Detalle de una carga\n"
        "  /active — Carga activa ahora\n\n"
        "🚨 *Alarmas*\n"
        "  /alarms — Alarmas activas\n"
        "  /alarms\\_all — Últimas 20 alarmas\n\n"
        "📊 *Sistema*\n"
        "  /status — Estado completo\n"
        "  /db — Tamaño DB + sync Supabase\n"
        "  /help — Esta ayuda\n\n"
        "🔍 *Búsqueda*\n"
        "  /search <pregunta> — Buscar en histórico",
        parse_mode="Markdown"
    )


async def cmd_temp(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    conn = get_db()
    row = conn.execute(
        "SELECT timestamp, furnace, temp_sales, temp_cameras, set_point "
        "FROM readings ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("📭 Sin lecturas en la base de datos")
        return

    ts = row["timestamp"]
    sales = row["temp_sales"] or 0
    cam = row["temp_cameras"] or 0
    sp = row["set_point"] or 0
    furnace = row["furnace"] or "?"

    # Time since last reading
    try:
        if "T" in ts:
            dt = datetime.fromisoformat(ts.replace("+02:00", "").replace("+01:00", ""))
        else:
            dt = datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
        ago = datetime.now() - dt
        ago_str = f"{int(ago.total_seconds())}s ago" if ago.total_seconds() < 120 else f"{int(ago.total_seconds()/60)}min ago"
    except:
        ago_str = "?"

    emoji_sales = "🔴" if sales > 600 else "🟡" if sales > 200 else "🟢" if sales > 0 else "⚪"
    emoji_cam = "🔴" if cam > 600 else "🟡" if cam > 200 else "🟢" if cam > 0 else "⚪"

    msg = (
        f"🌡️ *Temperatura Actual* — `{furnace}`\n\n"
        f"{emoji_sales} Sales: *{sales:.1f}°C*\n"
        f"{emoji_cam} Cámaras: *{cam:.1f}°C*\n"
        f"🎯 Set Point: *{sp:.1f}°C*\n\n"
        f"🕐 {ts[:19]} ({ago_str})"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_temp_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    hours = 8
    if ctx.args:
        try: hours = int(ctx.args[0])
        except: pass

    conn = get_db()
    rows = conn.execute(
        "SELECT timestamp, temp_sales, temp_cameras FROM readings "
        "WHERE timestamp >= datetime('now', ? || ' hours') ORDER BY timestamp ASC",
        (f"-{hours}",)
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text(f"📭 Sin lecturas en las últimas {hours}h")
        return

    temps_sales = [r["temp_sales"] or 0 for r in rows]
    temps_cam = [r["temp_cameras"] or 0 for r in rows]
    non_zero_sales = [t for t in temps_sales if t > 0]
    non_zero_cam = [t for t in temps_cam if t > 0]

    msg = (
        f"📊 *Temperaturas — Últimas {hours}h*\n"
        f"📏 {len(rows)} lecturas\n\n"
        f"🌡️ *Sales:*\n"
        f"  Min: {min(non_zero_sales):.1f}°C\n" if non_zero_sales else ""
        f"  Max: {max(non_zero_sales):.1f}°C\n" if non_zero_sales else ""
        f"  Media: {sum(non_zero_sales)/len(non_zero_sales):.1f}°C\n\n" if non_zero_sales else "\n"
        f"🌡️ *Cámaras:*\n"
        f"  Min: {min(non_zero_cam):.1f}°C\n" if non_zero_cam else ""
        f"  Max: {max(non_zero_cam):.1f}°C\n" if non_zero_cam else ""
        f"  Media: {sum(non_zero_cam)/len(non_zero_cam):.1f}°C" if non_zero_cam else ""
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_tracker(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM temperature_tracking").fetchone()[0]
    last = conn.execute(
        "SELECT timestamp, temperature, load_status FROM temperature_tracking ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    today_count = conn.execute(
        "SELECT COUNT(*) FROM temperature_tracking WHERE date = ?", (_today(),)
    ).fetchone()[0]
    conn.close()

    msg = (
        f"📡 *Temp Tracker*\n\n"
        f"📊 Total snapshots: {count}\n"
        f"📅 Hoy: {today_count}\n"
    )
    if last:
        msg += (
            f"\n🕐 Último: {last['timestamp'][:19]}\n"
            f"🌡️ Temp: {last['temperature'] or 0:.1f}°C\n"
            f"📦 Estado: {last['load_status'] or 'idle'}"
        )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_loads(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    today = _today()
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, furnace, start_time, end_time, status, ot_number, "
        "duration_s, total_minutes FROM loads WHERE date = ? ORDER BY id ASC",
        (today,)
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text(f"📭 Sin cargas hoy ({today})")
        return

    lines = [f"📦 *Cargas de hoy* ({today})\n"]
    for r in rows:
        emoji = "🟢" if r["status"] == "active" else "✅" if r["status"] == "completed" else "⏳"
        dur = ""
        if r["duration_s"]:
            mins = r["duration_s"] / 60
            dur = f" ({mins:.0f}min)"
        elif r["total_minutes"]:
            dur = f" ({r['total_minutes']:.0f}min)"
        ot = f" OT:{r['ot_number']}" if r["ot_number"] else ""
        lines.append(f"{emoji} #{r['id']} {r['name'][:30]}{ot}{dur}")

    active = sum(1 for r in rows if r["status"] == "active")
    completed = sum(1 for r in rows if r["status"] == "completed")
    lines.append(f"\nTotal: {len(rows)} | ✅{completed} | 🟢{active}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_loads_week(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    conn = get_db()
    rows = conn.execute(
        "SELECT date, COUNT(*) as cnt, "
        "SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as done, "
        "COALESCE(SUM(duration_s), 0) as total_s "
        "FROM loads WHERE date >= date('now', '-7 days') "
        "GROUP BY date ORDER BY date DESC"
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("📭 Sin cargas en los últimos 7 días")
        return

    lines = ["📅 *Cargas — Última semana*\n"]
    for r in rows:
        hrs = r["total_s"] / 3600 if r["total_s"] else 0
        lines.append(f"  {r['date']}: {r['cnt']} cargas ({r['done']}✅) — {hrs:.1f}h")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_load_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not ctx.args:
        await update.message.reply_text("Uso: /load <id>")
        return

    try:
        load_id = int(ctx.args[0])
    except:
        await update.message.reply_text("❌ ID debe ser un número")
        return

    conn = get_db()
    load = conn.execute("SELECT * FROM loads WHERE id = ?", (load_id,)).fetchone()
    if not load:
        conn.close()
        await update.message.reply_text(f"❌ Carga #{load_id} no encontrada")
        return

    subloads = conn.execute(
        "SELECT * FROM work_orders WHERE load_id = ? ORDER BY id", (load_id,)
    ).fetchall()
    conn.close()

    l = dict(load)
    emoji = "🟢" if l["status"] == "active" else "✅" if l["status"] == "completed" else "⏳"
    dur = f"{l['duration_s']/60:.0f}min" if l.get("duration_s") else "—"

    msg = (
        f"{emoji} *Carga #{load_id}*\n\n"
        f"📝 Nombre: {l['name']}\n"
        f"🏭 Horno: {l.get('furnace', '?')}\n"
        f"📅 Fecha: {l['date']}\n"
        f"🕐 Inicio: {(l.get('start_time') or '—')[:19]}\n"
        f"🕐 Fin: {(l.get('end_time') or '—')[:19]}\n"
        f"⏱️ Duración: {dur}\n"
        f"📋 OT: {l.get('ot_number') or '—'}\n"
        f"📊 Estado: {l['status']}\n"
    )

    if l.get("temp_start"):
        msg += f"🌡️ Temp inicio: {l['temp_start']}°C\n"
    if l.get("check_set_point"):
        msg += f"🎯 Set Point: {l['check_set_point']}°C\n"

    if subloads:
        msg += f"\n📦 *Subcargas ({len(subloads)}):*\n"
        for i, s in enumerate(subloads):
            s = dict(s)
            done = "✅" if s.get("done") else "⏳"
            dur_sub = f"{s.get('duration_min', 0) or s.get('required_min', 0)}min"
            ref = s.get("reference") or s.get("piece_ref") or "—"
            msg += f"  {done} Sub {i+1}: {s.get('ot_number','?')} | {dur_sub} | Ref: {ref}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_active(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    conn = get_db()
    load = conn.execute(
        "SELECT * FROM loads WHERE status = 'active' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if not load:
        await update.message.reply_text("📭 No hay carga activa en este momento")
        return

    # Reuse load detail
    ctx.args = [str(load["id"])]
    await cmd_load_detail(update, ctx)


async def cmd_alarms(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM alarms WHERE resolved = 0 ORDER BY timestamp DESC LIMIT 10"
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("✅ Sin alarmas activas")
        return

    lines = ["🚨 *Alarmas Activas*\n"]
    for r in rows:
        r = dict(r)
        lines.append(
            f"  🔴 #{r['id']} [{r['alarm_type']}]\n"
            f"     {r.get('details', '')[:60]}\n"
            f"     {r['timestamp'][:19]} — {r.get('furnace', '?')}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_alarms_all(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM alarms ORDER BY timestamp DESC LIMIT 20"
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("📭 Sin alarmas registradas")
        return

    lines = ["🚨 *Últimas 20 Alarmas*\n"]
    for r in rows:
        r = dict(r)
        emoji = "✅" if r.get("resolved") else "🔴"
        lines.append(f"  {emoji} #{r['id']} {r['alarm_type'][:20]} | {r['timestamp'][:16]}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    conn = get_db()

    # Last reading
    last_reading = conn.execute(
        "SELECT timestamp, temp_sales, temp_cameras FROM readings ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()

    # Active loads
    active_loads = conn.execute(
        "SELECT COUNT(*) FROM loads WHERE status = 'active'"
    ).fetchone()[0]

    # Today's loads
    today_loads = conn.execute(
        "SELECT COUNT(*) FROM loads WHERE date = ?", (_today(),)
    ).fetchone()[0]

    # Active alarms
    active_alarms = conn.execute(
        "SELECT COUNT(*) FROM alarms WHERE resolved = 0"
    ).fetchone()[0]

    # Total readings
    total_readings = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]

    # DB file size
    db_size_mb = os.path.getsize(DB_FILE) / 1024 / 1024

    conn.close()

    sales = last_reading["temp_sales"] or 0 if last_reading else 0
    cam = last_reading["temp_cameras"] or 0 if last_reading else 0
    ts = last_reading["timestamp"][:19] if last_reading else "—"

    alarm_emoji = "🔴" if active_alarms > 0 else "✅"

    msg = (
        f"📊 *TSC Nexus — Estado*\n\n"
        f"🌡️ *Temperatura:*\n"
        f"  Sales: {sales:.1f}°C | Cámaras: {cam:.1f}°C\n"
        f"  Última lectura: {ts}\n\n"
        f"📦 *Cargas:*\n"
        f"  Activas: {active_loads} | Hoy: {today_loads}\n\n"
        f"{alarm_emoji} *Alarmas activas:* {active_alarms}\n\n"
        f"💾 *Base de datos:*\n"
        f"  SQLite: {db_size_mb:.1f} MB | {total_readings} lecturas"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_db(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    import requests as req

    SUPABASE_URL_ENV = os.environ.get("SUPABASE_URL", "").rstrip("/")
    SUPABASE_KEY_ENV = os.environ.get("SUPABASE_ANON_KEY", "")

    conn = get_db()
    tables = ["readings", "loads", "events", "temperature_tracking", "alarms", "work_orders"]
    lines = ["💾 *Base de Datos — Sync Status*\n"]
    lines.append(f"📁 SQLite: `{os.path.getsize(DB_FILE)/1024:.0f} KB`\n")
    lines.append("| Tabla | SQLite | Supabase | Status |")
    lines.append("|---|---|---|---|")

    for table in tables:
        try:
            local = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except:
            local = "—"

        if SUPABASE_URL_ENV and SUPABASE_KEY_ENV:
            try:
                r = req.head(
                    f"{SUPABASE_URL_ENV}/rest/v1/{table}?select=*",
                    headers={"apikey": SUPABASE_KEY_ENV, "Authorization": f"Bearer {SUPABASE_KEY_ENV}",
                             "Prefer": "count=exact"}, timeout=10
                )
                remote = int(r.headers.get("Content-Range", "").split("/")[1])
            except:
                remote = "?"
        else:
            remote = "N/A"

        if isinstance(local, int) and isinstance(remote, int):
            status = "✅" if abs(local - remote) < 5 else f"⚠️ Δ{local-remote}"
        else:
            status = "?"

        lines.append(f"| `{table}` | {local} | {remote} | {status} |")

    conn.close()
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not ctx.args:
        await update.message.reply_text(
            "🔍 Uso: /search <pregunta>\n\n"
            "Ejemplos:\n"
            "  /search cargas de ayer\n"
            "  /search temperatura máxima hoy\n"
            "  /search alarmas de esta semana"
        )
        return

    query = " ".join(ctx.args).lower()
    conn = get_db()
    results = []

    # Simple keyword-based search (no LLM for now)
    if "carga" in query or "load" in query:
        rows = conn.execute(
            "SELECT id, name, date, status, furnace, ot_number FROM loads "
            "ORDER BY id DESC LIMIT 10"
        ).fetchall()
        if rows:
            results.append("📦 *Últimas cargas:*")
            for r in rows:
                r = dict(r)
                results.append(f"  #{r['id']} {r['name'][:25]} | {r['date']} | {r['status']}")

    elif "temp" in query or "grado" in query:
        rows = conn.execute(
            "SELECT timestamp, temp_sales, temp_cameras FROM readings "
            "WHERE temp_sales > 0 ORDER BY timestamp DESC LIMIT 10"
        ).fetchall()
        if rows:
            temps = [r["temp_sales"] for r in rows if r["temp_sales"]]
            results.append(f"🌡️ *Últimas temperaturas (Sales):*")
            results.append(f"  Rango: {min(temps):.0f}°C – {max(temps):.0f}°C")
            for r in rows[:5]:
                results.append(f"  {r['timestamp'][:16]} → {r['temp_sales']:.1f}°C")

    elif "alarm" in query:
        rows = conn.execute(
            "SELECT * FROM alarms ORDER BY timestamp DESC LIMIT 10"
        ).fetchall()
        if rows:
            results.append("🚨 *Últimas alarmas:*")
            for r in rows:
                r = dict(r)
                emoji = "✅" if r.get("resolved") else "🔴"
                results.append(f"  {emoji} {r['alarm_type']} | {r['timestamp'][:16]}")
    else:
        results.append(
            "🤔 No entendí la búsqueda.\n\n"
            "Prueba con: cargas, temperaturas, alarmas"
        )

    conn.close()
    await update.message.reply_text("\n".join(results) if results else "📭 Sin resultados", parse_mode="Markdown")


# ── Main ──────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        print("❌ TSC_TELEGRAM_BOT_TOKEN not set in .env")
        sys.exit(1)

    log.info(f"🏭 TSC_Nexus_MonitorBot starting... Token: ...{BOT_TOKEN[-6:]}")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_help))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("temp", cmd_temp))
    app.add_handler(CommandHandler("temp_history", cmd_temp_history))
    app.add_handler(CommandHandler("tracker", cmd_tracker))
    app.add_handler(CommandHandler("loads", cmd_loads))
    app.add_handler(CommandHandler("loads_week", cmd_loads_week))
    app.add_handler(CommandHandler("load", cmd_load_detail))
    app.add_handler(CommandHandler("active", cmd_active))
    app.add_handler(CommandHandler("alarms", cmd_alarms))
    app.add_handler(CommandHandler("alarms_all", cmd_alarms_all))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("db", cmd_db))
    app.add_handler(CommandHandler("search", cmd_search))

    log.info("✅ TSC_Nexus_MonitorBot ready — polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
