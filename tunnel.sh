#!/bin/bash

# Plan B: Serveo (No token needed!)

# 0. Kill existing uvicorn to free port 80 (just in case)
pkill -f uvicorn

# 1. Start server silently
nohup ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 80 > /dev/null 2>&1 &

# 2. Start Tunnel
echo "Starting Serveo... Copy the URL below (e.g. https://abcd.serveo.net)"
ssh -o StrictHostKeyChecking=no -R 80:localhost:80 serveo.net
