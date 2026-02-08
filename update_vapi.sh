# Usage: bash update_vapi.sh [OPTIONAL_KEY]

# Default to the key provided by user (for ease of use)
DEFAULT_KEY="e3c5a54b-de3c-4c86-bcb0-ac08bf2a900a"

KEY=${1:-$DEFAULT_KEY}

# Append or replace VAPI_PRIVATE_KEY in .env
# Remove existing VAPI_PRIVATE_KEY line if present
sed -i '/VAPI_PRIVATE_KEY/d' .env

# Add new key
echo "VAPI_PRIVATE_KEY=$KEY" >> .env

echo "✅ Vapi Key updated to: $KEY"
echo "✅ OpenAI Key preserved."
