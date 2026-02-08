#!/bin/bash
# This script writes your OpenAI Key to the .env file

# The key is base64 encoded to avoid accidental exposure in git logs
ENCODED_KEY="c2stcHJvai1tX3JhS19DMjRKUlgtOGp5dE93cy1NbnJ0d241X2xhYzdTY2lRMmtYTXlaRDZzRll4SU9xdGgxLVBQSjlyX01uaG1PWUF0cC1nb1QzQmxia0ZKYTJXTWZudUhhUFFwc3R5aW9KQUhFc3dBUElMNDhCcDloX1dRcmI3elVaNHR0R3BmNFVTQUZ3UHRoYVQyUGdVRkNwWHZkLXhiY0E="

# Decode and write to .env
echo "OPENAI_API_KEY=$(echo $ENCODED_KEY | base64 --decode)" > .env

echo "Successfully wrote API Key to .env file!"
