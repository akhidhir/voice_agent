#!/bin/bash
echo "--- Checking System Status ---"
echo "1. Checking Uvicorn (Python App)..."
ps aux | grep uvicorn | grep -v grep

echo -e "\n2. Checking Caddy (Web Server)..."
ps aux | grep caddy | grep -v grep

echo -e "\n3. Testing App Locally (Port 5050)..."
curl -I http://127.0.0.1:5050/

echo -e "\n4. Testing Public HTTPS..."
curl -I https://43.229.61.225.sslip.io/incoming-call

echo -e "\n5. App Logs (Last 20 lines)..."
tail -n 20 app.log
