#!/bin/bash
# ============================================================
# TSC MiniPC Auto-Setup Script
# Run this ON the MiniPC after SSH-ing in
# Usage: bash setup_minipc.sh
# ============================================================
set -e

echo "╔═══════════════════════════════════════════════╗"
echo "║  TSC MiniPC — Auto Setup Script               ║"
echo "║  Fecha: $(date '+%Y-%m-%d %H:%M')                      ║"
echo "╚═══════════════════════════════════════════════╝"

# ─── 1. System update ────────────────────────────────────────
echo ""
echo "▸ [1/7] Actualizando sistema..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv curl git

# ─── 2. App directory ────────────────────────────────────────
echo "▸ [2/7] Configurando directorio..."
APP_DIR="$HOME/tsc"
mkdir -p "$APP_DIR/data"
cd "$APP_DIR"

# ─── 3. Python dependencies ──────────────────────────────────
echo "▸ [3/7] Instalando dependencias Python..."
pip3 install --quiet flask python-dotenv pymodbus requests resend

# ─── 4. Check .env ───────────────────────────────────────────
echo "▸ [4/7] Verificando .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" << 'ENVEOF'
# TSC Configuration
FURNACES=sulfur_1,sulfur_2,oxidation_1
DEFAULT_TIMER=1800
PORT=8080
SECRET_KEY=tsc-secret-2026
ADMIN_PASS=tsc2026

# Supabase (dual-write)
SUPABASE_URL=https://httfohqoikkptywupkrs.supabase.co
SUPABASE_ANON_KEY=YOUR_KEY_HERE

# Email notifications (Resend)
RESEND_API_KEY=YOUR_KEY_HERE
RESEND_FROM=tsc@movildrive.com
RESEND_TO=hola@movildrive.com
ENVEOF
    echo "  ⚠️  .env creado con valores por defecto — edita SUPABASE_ANON_KEY y RESEND_API_KEY"
else
    echo "  ✅ .env ya existe"
fi

# ─── 5. Check RS-485 ─────────────────────────────────────────
echo "▸ [5/7] Verificando RS-485..."
if ls /dev/ttyUSB0 2>/dev/null; then
    echo "  ✅ Waveshare detectado en /dev/ttyUSB0"
    # Permisos para acceder al puerto serie
    sudo usermod -a -G dialout $USER 2>/dev/null || true
else
    echo "  ⚠️  /dev/ttyUSB0 no encontrado — conecta el cable USB del Waveshare"
fi

# ─── 6. Install Ollama (LLM) ─────────────────────────────────
echo "▸ [6/7] Instalando Ollama..."
if command -v ollama &> /dev/null; then
    echo "  ✅ Ollama ya instalado: $(ollama --version)"
else
    echo "  Descargando e instalando Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "  ✅ Ollama instalado"
fi

# Download model (background — takes a few minutes)
echo "  Descargando modelo phi3:mini (~2.3GB)..."
ollama pull phi3:mini &
OLLAMA_PID=$!
echo "  ⏳ Descargando en background (PID: $OLLAMA_PID)"

# ─── 7. Create systemd service ───────────────────────────────
echo "▸ [7/7] Configurando arranque automático..."
sudo tee /etc/systemd/system/tsc.service > /dev/null << SVCEOF
[Unit]
Description=TSC Furnace Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=/usr/bin/python3 $APP_DIR/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable tsc.service
echo "  ✅ Servicio tsc.service creado y habilitado"

# ─── Summary ─────────────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║  ✅ SETUP COMPLETADO                          ║"
echo "╠═══════════════════════════════════════════════╣"
echo "║  App dir:    $APP_DIR"
echo "║  Puerto:     :8080"
echo "║  Servicio:   sudo systemctl start tsc"
echo "║  Logs:       journalctl -u tsc -f"
echo "║  Ollama:     esperando descarga de phi3:mini"
echo "╚═══════════════════════════════════════════════╝"
echo ""
echo "▸ Para arrancar AHORA:"
echo "  cd $APP_DIR && python3 app.py"
echo ""
echo "▸ Para arrancar como servicio:"
echo "  sudo systemctl start tsc"
echo "  sudo systemctl status tsc"
