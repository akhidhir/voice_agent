#!/bin/bash

# 1. authenticate ngrok (User provided token)
ngrok config add-authtoken 39NtAgOQMZFvC4M6PZP3M8JtRGY_5tmZyLrHDhGcZBrHNAXja

# 2. Start Uvicorn in background (silently)
nohup ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 80 > /dev/null 2>&1 &

# 3. Start ngrok tunnel
echo "Starting ngrok tunnel..."
ngrok http 80
