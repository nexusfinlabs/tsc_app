#!/bin/bash
# ─────────────────────────────────────────────────────────────
# TSC Health Check — Monitores HTTPS endpoint + app.py + email alerts
# Runs every 2 minutes via cron. Sends email via Resend if endpoint is down.
#
# Install:
#   crontab -e
#   */2 * * * * /home/tsc/tsc_app/health_check.sh >> /home/tsc/tsc_app/logs/health.log 2>&1
# ─────────────────────────────────────────────────────────────

ENDPOINT="https://tsc.tail8dce43.ts.net/"
APP_DIR="/home/tsc/tsc_app"
APP_CMD="python3 ${APP_DIR}/app.py"
LOG_FILE="${APP_DIR}/logs/health.log"
LOCK_FILE="/tmp/tsc_health_alert.lock"  # Prevent spam (1 email per 10 min)
RESEND_API_KEY="re_PJ4SJgLF_KJXVutpAfyoEWsjdpB8ncJfg"
NOTIFY_FROM="TSC Monitor <onboarding@resend.dev>"
NOTIFY_TO='["alebronlobo81@gmail.com","d.serrano.9080@gmail.com"]'

mkdir -p "${APP_DIR}/logs"
NOW=$(date '+%Y-%m-%d %H:%M:%S')

# ─── 1. Check if app.py is running ──────────────────────────
APP_RUNNING=$(pgrep -f "${APP_DIR}/app.py" | head -1)
if [ -z "$APP_RUNNING" ]; then
    echo "[$NOW] ⚠️  app.py NOT running — restarting..."
    cd "$APP_DIR"
    nohup python3 app.py >> app.log 2>&1 &
    sleep 3
    APP_RUNNING=$(pgrep -f "${APP_DIR}/app.py" | head -1)
    if [ -z "$APP_RUNNING" ]; then
        echo "[$NOW] ❌ app.py FAILED to start"
    else
        echo "[$NOW] ✅ app.py restarted (PID: $APP_RUNNING)"
    fi
fi

# ─── 2. Check if Tailscale Serve is pointing to :5000 ───────
SERVE_STATUS=$(tailscale serve status 2>&1)
if echo "$SERVE_STATUS" | grep -q "127.0.0.1:5000"; then
    : # OK
else
    echo "[$NOW] ⚠️  Tailscale Serve not pointing to :5000 — fixing..."
    tailscale serve --bg --https=443 http://localhost:5000 2>&1
    tailscale funnel --bg 443 2>&1
    echo "[$NOW] ✅ Tailscale Serve/Funnel reconfigured"
fi

# ─── 3. Check HTTPS endpoint ────────────────────────────────
HTTP_CODE=$(curl -sI --max-time 10 "$ENDPOINT" 2>/dev/null | head -1 | awk '{print $2}')
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "[$NOW] ✅ Endpoint OK (HTTP $HTTP_CODE)"
    # Remove lock if endpoint recovered
    rm -f "$LOCK_FILE"
    exit 0
fi

echo "[$NOW] ❌ Endpoint DOWN (HTTP: ${HTTP_CODE:-timeout})"

# ─── 4. Send alert email (max 1 per 10 minutes) ─────────────
if [ -f "$LOCK_FILE" ]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0) ))
    if [ "$LOCK_AGE" -lt 600 ]; then
        echo "[$NOW] 📧 Alert already sent ${LOCK_AGE}s ago — skipping"
        exit 1
    fi
fi

# Send email via Resend API
SUBJECT="🚨 TSC ENDPOINT DOWN — ${NOW}"
HTML_BODY="<h2 style='color:#ef4444'>⚠️ TSC Monitor — Endpoint Caído</h2>\
<p><b>Endpoint:</b> <a href='${ENDPOINT}'>${ENDPOINT}</a></p>\
<p><b>Estado HTTP:</b> ${HTTP_CODE:-timeout}</p>\
<p><b>Hora:</b> ${NOW}</p>\
<p><b>Servidor:</b> MiniPC TSC (100.104.65.25)</p>\
<hr>\
<p>El sistema intentó reiniciar automáticamente app.py y Tailscale Serve.</p>\
<p>Si recibes este email, comprueba el MiniPC físicamente o conecta via:</p>\
<pre>ssh tsc-jump</pre>\
<p style='color:#64748b;font-size:12px'>— TSC Health Monitor (cron cada 2 min)</p>"

PAYLOAD=$(cat <<EOF
{
  "from": "${NOTIFY_FROM}",
  "to": ${NOTIFY_TO},
  "subject": "${SUBJECT}",
  "html": "${HTML_BODY}"
}
EOF
)

RESPONSE=$(curl -s -X POST "https://api.resend.com/emails" \
  -H "Authorization: Bearer ${RESEND_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}" 2>&1)

echo "[$NOW] 📧 Alert email sent: $RESPONSE"
touch "$LOCK_FILE"
