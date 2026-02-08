import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.websockets import WebSocketDisconnect
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
load_dotenv()

# Hardcoded for VPS deployment ease (Temporary)
# API Key is loaded from .env (See setup_key.sh)
pass

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 5050))

SYSTEM_MESSAGE = (
    "You are Sarah, a warm and professional scheduling assistant for ABBC Building Inspectors in Perth. "
    "Your goal is to help clients book the right inspection for their needs. "
    "You work for Andrew Booth (Registered Builder 9179). "
    "ALWAYS ask clarifying questions to give an accurate quote. "
    "Prices start at $495 but depend on house size. "
    "If they ask for a price, ask: 'Is it a single or double storey home?' and 'How many bedrooms and bathrooms?'. "
    "If they are buying a home, recommend the Pre-Purchase Inspection. "
    "If they are building a new home, recommend Under Construction Inspections (Slab, Plate, Roof, Lockup, Handover). "
    "Always offer a Pest Inspection upscale for +$150. "
    "Keep your responses concise and conversational. Do not use jargon. "
    "If asked about availability, check the calendar using the tool."
)

VOICE = 'shimmer' # A warm female voice
LOG_EVENT_TYPES = [
    'response.content.done',
    'rate_limits.updated',
    'response.done',
    'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started',
    'session.created'
]

app = FastAPI()

if not OPENAI_API_KEY:
    raise ValueError('Missing the OPENAI_API_KEY environment variable.')

@app.get("/", response_class=HTMLResponse)
async def index_page():
    return "<html><body><h1>ABBC Voice Agent Server</h1></body></html>"

@app.post("/incoming-call")
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    host = request.headers.get('host')
    # Use standard TwiML XML format
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://{host}/media-stream" />
    </Connect>
</Response>"""
    return Response(content=xml_content, media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connection between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await send_session_update(openai_ws)
        stream_sid = None

        async def receive_from_twilio():
            """Receive audio data from Twilio and send to OpenAI."""
            nonlocal stream_sid
            try:
                chunk_count = 0
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media':
                        chunk_count += 1
                        if chunk_count % 50 == 0:
                            print(f"Received 50 audio chunks from Twilio...")
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")

                        # Trigger the AI to speak first (Greeting)
                        # We do this here to ensure we have the stream_sid to send audio back
                        print("Triggering initial greeting...")
                        await openai_ws.send(json.dumps({
                            "type": "response.create",
                            "response": {
                                "modalities": ["text", "audio"],
                                "instructions": "Say 'Hi, this is Sarah from ABBC Building Inspectors. How can I help you today?'"
                            }
                        }))
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from OpenAI and send audio back to Twilio."""
            nonlocal stream_sid
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    
                    # Log EVERYTHING for debugging (except raw audio deltas which are huge)
                    if response['type'] != 'response.audio.delta':
                        print(f"OpenAI Event: {response['type']}")

                    if response['type'] == 'session.updated':
                        print("Session updated successfully:", response)

                    if response['type'] == 'response.audio.delta' and response.get('delta'):
                        if stream_sid:
                            # print(".", end="", flush=True) # visual indicator of audio flow
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": response['delta']
                                }
                            }
                            await websocket.send_json(audio_delta)
                        else:
                            print("Warning: Received audio but no stream_sid yet!")
                    
                    # Handle Function Calling
                    if response['type'] == 'response.done':
                         print("Response generation done.")
                         if response.get('response', {}).get('output'):
                            for item in response['response']['output']:
                                if item.get('type') == 'function_call':
                                    await handle_function_call(item, openai_ws)

            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def send_session_update(openai_ws):
    """Send session update to OpenAI WebSocket."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500
            },
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            "tools": [
                {
                    "type": "function",
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
                {
                    "type": "function",
                    "name": "check_availability",
                    "description": "Check available inspection slots.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "Date to check availability for"}
                        }
                    }
                }
            ],
            "tool_choice": "auto",
        }
    }
    print('Sending session update...')
    await openai_ws.send(json.dumps(session_update))

async def handle_function_call(item, openai_ws):
    """Execute the function and send result back to OpenAI."""
    call_id = item['call_id']
    function_name = item['name']
    try:
        arguments = json.loads(item['arguments'])
    except:
        arguments = {}
    
    print(f"Calling function: {function_name} with args: {arguments}")
    
    result = None
    if function_name == "calculate_quote":
        base_price = 495
        if arguments.get('is_double_storey'):
            base_price += 100
        if arguments.get('bedrooms', 0) > 4:
            base_price += 50
        result = {"price": base_price, "currency": "AUD", "note": "Includes GST"}
    
    elif function_name == "check_availability":
        # Mock availability
        result = {"available_slots": ["9:00 AM", "2:00 PM"], "date": arguments.get('date')}

    # Send result back
    function_output = {
        "type": "conversation.item.create",
        "item": {
            "type": "function_call_output",
            "call_id": call_id,
            "output": json.dumps(result)
        }
    }
    await openai_ws.send(json.dumps(function_output))
    
    # Trigger AI specific response to the function output
    await openai_ws.send(json.dumps({"type": "response.create"}))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
