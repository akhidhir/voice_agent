#!/bin/bash
# Usage: bash update_vapi.sh <VAPI_PRIVATE_KEY>

if [ -z "$1" ]; then
    echo "Usage: bash update_vapi.sh <VAPI_PRIVATE_KEY>"
    exit 1
fi

# Append or replace VAPI_PRIVATE_KEY in .env
# Remove existing VAPI_PRIVATE_KEY line if present
sed -i '/VAPI_PRIVATE_KEY/d' .env

# Add new key
echo "VAPI_PRIVATE_KEY=$1" >> .env

echo "✅ Vapi Key updated! (OpenAI Key preserved)"
