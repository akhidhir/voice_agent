#!/bin/bash

# Plan D: Localtunnel (via Node.js)
# 1. Install Node.js & NPM (if missing)
if ! command -v npm &> /dev/null; then
    echo "Installing Node.js (one-time setup)..."
    sudo apt update
    sudo apt install nodejs npm -y
fi

# 2. Start server silently
pkill -f uvicorn
nohup ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 80 > /dev/null 2>&1 &

# 3. Start Tunnel
echo "Starting Localtunnel... Copy the URL below:"
npx localtunnel --port 80
