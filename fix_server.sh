#!/bin/bash

echo "1. Cleaning up mess (stopping old processes)..."
sudo pkill -f uvicorn
sudo pkill -f caddy
sudo systemctl stop caddy

echo "2. Configuring Caddy correctly (Systemd)..."
# Write Caddyfile
sudo bash -c 'cat > /etc/caddy/Caddyfile <<EOF
43.229.61.225.sslip.io {
    reverse_proxy localhost:5050
}
EOF'

echo "3. Restarting Web Server..."
sudo systemctl start caddy
sudo systemctl enable caddy

echo "4. Starting Voice Agent (Port 5050)..."
nohup ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 5050 > app.log 2>&1 &

echo "5. Waiting for certificate..."
sleep 5

echo "--- Server Status ---"
sudo systemctl status caddy --no-pager | grep "Active:"
echo "---------------------"
echo "Should be working now!"
