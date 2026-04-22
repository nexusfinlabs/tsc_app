"""
TSC Notifier — Email notifications via Resend HTTP API
Sends formatted HTML emails on LOAD_START and LOAD_STOP events.
No pip install needed — uses stdlib urllib.

Environment variables:
  RESEND_API_KEY   — Resend API key (re_xxxx)
  NOTIFY_TO        — Comma-separated recipient emails
  NOTIFY_FROM      — Sender email (default: TSC Monitor <onboarding@resend.dev>)
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime
import threading

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
NOTIFY_TO = os.getenv("NOTIFY_TO", "").split(",")
NOTIFY_FROM = os.getenv("NOTIFY_FROM", "TSC Monitor <onboarding@resend.dev>")

def _send_email(subject, html_body):
    """Send email via Resend HTTP API (non-blocking, fire-and-forget)."""
    if not RESEND_API_KEY or not any(NOTIFY_TO):
        print(f"[NOTIFY] ⚠️ Skipped — missing RESEND_API_KEY or NOTIFY_TO")
        return

    recipients = [e.strip() for e in NOTIFY_TO if e.strip()]
    payload = json.dumps({
        "from": NOTIFY_FROM,
        "to": recipients,
        "subject": subject,
        "html": html_body
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            print(f"[NOTIFY] ✅ Email sent: {subject} → {recipients} (id: {result.get('id','')})")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"[NOTIFY] ❌ HTTP {e.code}: {body}")
    except Exception as e:
        print(f"[NOTIFY] ❌ Error: {e}")


def _send_async(subject, html_body):
    """Fire-and-forget email in background thread."""
    threading.Thread(target=_send_email, args=(subject, html_body), daemon=True).start()


def _format_time():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def _base_html(title_emoji, title_text, color, details_rows):
    """Generate a clean, modern HTML email template."""
    rows_html = ""
    for label, value in details_rows:
        rows_html += f"""
        <tr>
          <td style="padding:10px 16px;font-size:14px;color:#666;border-bottom:1px solid #f0f0f0;width:40%">{label}</td>
          <td style="padding:10px 16px;font-size:14px;color:#222;font-weight:600;border-bottom:1px solid #f0f0f0">{value}</td>
        </tr>"""

    return f"""
    <div style="max-width:500px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
      <div style="background:{color};padding:24px 20px;border-radius:16px 16px 0 0;text-align:center">
        <div style="font-size:36px;margin-bottom:8px">{title_emoji}</div>
        <h1 style="margin:0;font-size:22px;color:#fff;font-weight:700">{title_text}</h1>
        <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,.7)">{_format_time()}</p>
      </div>
      <div style="background:#fff;border:1px solid #e5e5e5;border-top:none;border-radius:0 0 16px 16px;overflow:hidden">
        <table style="width:100%;border-collapse:collapse">
          {rows_html}
        </table>
      </div>
      <p style="text-align:center;margin-top:16px;font-size:11px;color:#aaa">
        TSC Monitor — <a href="https://tsc.tail8dce43.ts.net" style="color:#888">tsc.tail8dce43.ts.net</a>
      </p>
    </div>
    """


def notify_start(furnace, load_name, ot_number="", duration_min=120, **extra):
    """
    Send START notification email.

    Args:
        furnace: furnace name (e.g. 'sulfur_1')
        load_name: load name (e.g. 'Carga 7')
        ot_number: work order number (e.g. 'OT-120')
        duration_min: timer duration in minutes
        **extra: future fields (client_id, client_name, piece_ref, etc.)
    """
    subject = f"🟢 START — {load_name} [{furnace}] | {ot_number}"

    rows = [
        ("🏭 Horno", furnace),
        ("📋 Carga", load_name),
        ("🔖 Orden de Trabajo", ot_number or "—"),
        ("⏱ Duración programada", f"{duration_min} min"),
    ]

    # Future extensible fields
    if extra.get("client_name"):
        rows.append(("👤 Cliente", extra["client_name"]))
    if extra.get("client_id"):
        rows.append(("🆔 ID Cliente", extra["client_id"]))
    if extra.get("piece_ref"):
        rows.append(("🔩 Referencia pieza", extra["piece_ref"]))
    if extra.get("process"):
        rows.append(("⚙️ Proceso", extra["process"]))
    if extra.get("temperature"):
        rows.append(("🌡️ Temp. actual", f"{extra['temperature']}°C"))

    html = _base_html("🟢", f"CARGA INICIADA — {furnace}", "#16a34a", rows)
    _send_async(subject, html)


def notify_stop(furnace, load_name, duration_s=0, ot_number="", **extra):
    """
    Send STOP notification email.

    Args:
        furnace: furnace name
        load_name: load name
        duration_s: actual elapsed time in seconds
        ot_number: work order number
        **extra: future fields
    """
    mins = round(duration_s / 60, 1) if duration_s else 0
    subject = f"🔴 STOP — {load_name} [{furnace}] | {ot_number} | {mins}min"

    rows = [
        ("🏭 Horno", furnace),
        ("📋 Carga", load_name),
        ("🔖 Orden de Trabajo", ot_number or "—"),
        ("⏱ Duración real", f"{mins} min ({duration_s}s)"),
    ]

    if extra.get("client_name"):
        rows.append(("👤 Cliente", extra["client_name"]))
    if extra.get("client_id"):
        rows.append(("🆔 ID Cliente", extra["client_id"]))
    if extra.get("avg_temp"):
        rows.append(("🌡️ Temp. media", f"{extra['avg_temp']}°C"))
    if extra.get("max_temp"):
        rows.append(("🌡️ Temp. máxima", f"{extra['max_temp']}°C"))

    html = _base_html("🔴", f"CARGA FINALIZADA — {furnace}", "#dc2626", rows)
    _send_async(subject, html)


# ─── Self-test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"RESEND_API_KEY: {'✅ set' if RESEND_API_KEY else '❌ missing'}")
    print(f"NOTIFY_TO: {NOTIFY_TO}")
    print("Sending test email...")
    notify_start("sulfur_1", "Carga Test", ot_number="OT-140", duration_min=90)
    import time; time.sleep(3)
    notify_stop("sulfur_1", "Carga Test", duration_s=5400, ot_number="OT-140")
    time.sleep(3)
    print("Done.")
