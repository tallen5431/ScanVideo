#!/usr/bin/env bash
set -euo pipefail

# =====================================
# Enhanced CamScan Starter (Linux)
# - Creates/uses .venv
# - Installs requirements.txt
# - Runs app.py with HOST/PORT/CAM_INDEX
# =====================================

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

VENV_DIR="$APP_DIR/.venv"
PYTHON_EXE="$VENV_DIR/bin/python"

# Create venv if needed
if [ ! -x "$PYTHON_EXE" ]; then
    echo "[SETUP] Creating virtual environment for Enhanced CamScan..."
    python3 -m venv "$VENV_DIR"
fi

echo "[SETUP] Ensuring dependencies from requirements.txt..."
"$PYTHON_EXE" -m pip install --upgrade pip setuptools wheel >/dev/null
if [ -f "$APP_DIR/requirements.txt" ]; then
    "$PYTHON_EXE" -m pip install -r "$APP_DIR/requirements.txt"
fi

# Defaults (can be overridden by Server_Manager env)
: "${HOST:=0.0.0.0}"
: "${PORT:=8091}"
: "${CAM_INDEX:=0}"

export HOST PORT CAM_INDEX

echo ""
echo "=========================================="
echo "  Enhanced CamScan - Measurement System"
echo "=========================================="
echo "Server: ${HOST}:${PORT}"
echo "Camera: ${CAM_INDEX}"
echo "Calibration Square: 30mm"
echo ""
echo "Open in browser:"
echo "  http://localhost:${PORT}"
echo "  http://$(hostname -I | awk '{print $1}'):${PORT}"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

exec "$PYTHON_EXE" app.py
