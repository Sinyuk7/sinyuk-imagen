#!/usr/bin/env bash
set -e

echo "========================================"
echo "  Sinyuk Imagen - Starting..."
echo "========================================"
echo

# Check if .env exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "[INFO] .env not found, copying from .env.example..."
        cp .env.example .env
        echo "[WARN] Please edit .env and fill in your API keys, then re-run this script."
        exit 1
    fi
fi

# Create venv if not exists
if [ ! -d .venv ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "[INFO] Checking dependencies..."
pip install -r requirements.txt -q

# Launch app
echo
echo "[INFO] Launching app..."
echo
python app.py
