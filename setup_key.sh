#!/bin/bash
# This script writes your OpenAI Key to the .env file

# Usage: bash setup_key.sh <OPENAI_API_KEY> <VAPI_PRIVATE_KEY>

if [ -z "$1" ]; then
    echo "Usage: bash setup_key.sh <OPENAI_API_KEY> <VAPI_PRIVATE_KEY>"
    exit 1
fi

# Write to .env
echo "OPENAI_API_KEY=$1" > .env
if [ -n "$2" ]; then
    echo "VAPI_PRIVATE_KEY=$2" >> .env
fi
echo "PORT=5050" >> .env

echo "✅ Keys configured in .env file!"
