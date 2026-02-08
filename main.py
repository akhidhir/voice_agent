import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

# Vapi will call our server to get the Assistant Configuration
# And call our server again to execute Tools.

app = FastAPI()

PORT = int(os.getenv('PORT', 5050))
VAPI_PRIVATE_KEY = os.getenv('VAPI_PRIVATE_KEY')

# --- CONFIGURATION ---
SYSTEM_MESSAGE = (
    "You are Sarah, a warm and professional scheduling assistant for ABBC Building Inspectors in Perth, Western Australia. "
    "You communicate with a friendly Australian accent. "
    "Your goal is to help clients book the right inspection for their needs. "
    "You work for Andrew Booth (Registered Builder 9179). "
    "ALWAYS ask clarifying questions to give an accurate quote. "
    "Start by saying 'G'day! This is Sarah from ABBC Building Inspectors. How can I help you?' "
    "Prices start at $495 but depend on house size. "
    "If they ask for a price, ask: 'Is it a single or double storey home?' and 'How many bedrooms and bathrooms?'. "
    "If they are buying a home, recommend the Pre-Purchase Inspection. "
    "If they are building a new home, recommend Under Construction Inspections (Slab, Plate, Roof, Lockup, Handover). "
    "Always offer a Pest Inspection upscale for +$150. "
    "Keep your responses concise and conversational. Do not use jargon. "
    "If asked about availability, check the calendar using the tool."
    "IMPORTANT: Keep sentences short and punchy."
)

# Using ElevenLabs voice via Vapi
# User provided Voice ID: likely an Australian accent or similar high-quality voice
VOICE_ID = "sx8pHRzXdQfuUYPGFK7X"

@app.get("/")
async def index_page():
    return {"status": "Vapi Agent Server Running"}

@app.post("/incoming-call")
async def handle_incoming_call(request: Request):
    """
    Called by Vapi when a call starts (if configured as Server URL).
    Returns the Assistant Configuration.
    """
    host = request.headers.get('host') or "43.229.61.225.sslip.io"
    # Ensure HTTPS
    server_url = f"https://{host}"
    
    assistant_config = {
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en"
        },
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_MESSAGE
                }
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "calculate_quote",
                        "description": "Calculate the inspection price based on house details.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "bedrooms": {"type": "integer"},
                                "bathrooms": {"type": "integer"},
                                "is_double_storey": {"type": "boolean"},
                                "inspection_type": {"type": "string", "enum": ["pre_purchase", "under_construction"]}
                            },
                            "required": ["bedrooms", "bathrooms", "is_double_storey", "inspection_type"]
                        }
                    },
                    "server": {
                        "url": f"{server_url}/tool-call"
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "check_availability",
                        "description": "Check available inspection slots.",
                        "parameters": {
                             "type": "object",
                             "properties": {
                                 "date": {"type": "string", "description": "Date to check availability for"}
                             }
                        }
                    },
                    "server": {
                        "url": f"{server_url}/tool-call"
                    }
                }
            ]
        },
        "voice": {
            "provider": "11labs",
            "voiceId": VOICE_ID,
            "stability": 0.5,
            "similarityBoost": 0.75
        },
        "firstMessage": "G'day! This is Sarah from ABBC Building Inspectors. How can I help you?"
    }
    
    return JSONResponse(content=assistant_config)

@app.post("/tool-call")
async def handle_tool_call(request: Request):
    """
    Called by Vapi when the model decides to call a tool.
    """
    payload = await request.json()
    function_call = payload.get('message', {}).get('functionCall', {})
    
    name = function_call.get('name')
    parameters = function_call.get('parameters', {})
    
    print(f"Tool Call: {name} with {parameters}")
    
    result = {}
    
    if name == "calculate_quote":
        base_price = 495
        if parameters.get('is_double_storey'):
            base_price += 100
        if parameters.get('bedrooms', 0) > 4:
            base_price += 50
        result = {
            "result": f"${base_price} AUD (inc GST)",
            "breakdown": "Standard Fee + Extras"
        }
    
    elif name == "check_availability":
        result = {
            "available_slots": ["9:00 AM", "2:00 PM", "4:30 PM"],
            "date": parameters.get('date', 'today')  
        }
        
    return JSONResponse(content=result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
