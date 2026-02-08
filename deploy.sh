#!/bin/bash

# 1. Update Server
sudo apt update && sudo apt upgrade -y

# 2. Install Python & Pip
sudo apt install python3-pip python3-venv git -y

# 3. Clone Repository
git clone https://github.com/akhidhir/voice_agent.git
cd voice_agent

# 4. Create Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 5. Install Dependencies
pip install fastapi uvicorn websockets python-dotenv twilio

# 6. Create .env file
echo "OPENAI_API_KEY=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" > .env
echo "PORT=80" >> .env

# 7. Allow Port 80 through Firewall
sudo ufw allow 80

# 8. Start Server (Run in background using nohup or screen)
# sudo ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 80
