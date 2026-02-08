#!/bin/bash

# Plan E: Native SSL with Caddy (The Professional Way)
# No tunnels needed!

# 1. Install Caddy (Web Server with Auto-HTTPS)
if ! command -v caddy &> /dev/null; then
    echo "Installing Caddy..."
    sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
    sudo apt update
    sudo apt install caddy -y
fi

# 2. Start Python Server on Port 5050 (So Caddy can use Port 80/443)
pkill -f uvicorn
export PORT=5050
nohup ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 5050 > /dev/null 2>&1 &

# 3. Configure Caddy to proxy 443 -> 5050
# We use sslip.io which points to your IP automatically!
DOMAIN="43.229.61.225.sslip.io"

echo "Configuring Caddy for $DOMAIN..."
sudo caddy stop
sudo caddy reverse-proxy --from $DOMAIN --to :5050 > /dev/null 2>&1 &

echo "---------------------------------------------------"
echo "Done! Your Secure URL is:"
echo "https://$DOMAIN/incoming-call"
echo "---------------------------------------------------"
echo "Paste that into Twilio!"
