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
    "IMPORTANT: If the user interrupts you, stop speaking immediately and listen."
    "Do not repeat yourself. Be direct."
)

# ... (omitted lines) ...

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

                    # Log specific events with MORE detail
                    if response['type'] == 'error':
                        print(f"!!! ERROR !!!: {json.dumps(response, indent=2)}")

                    if response['type'] == 'input_audio_buffer.speech_started':
                        print("Speech started detected! Clearing Twilio buffer...")
                        # CLEAR Twilio buffer immediately for crisp interruption
                        if stream_sid:
                            await websocket.send_json({
                                "event": "clear",
                                "streamSid": stream_sid
                            })
                        
                        # Also cancel any ongoing response generation
                        await openai_ws.send(json.dumps({"type": "response.cancel"}))

                    if response['type'] == 'conversation.item.input_audio_transcription.completed':
                        transcript = response.get('transcript', '((No transcript))')
                        print(f"TRANSCRIPTION: {transcript}")
                        # FORCE the model to respond if it heard something
                        if transcript.strip():
                            print("Forcing response generation...")
                            await openai_ws.send(json.dumps({"type": "response.create"}))

                    if response['type'] == 'response.done':
                         # Print the WHOLE object to see status/failure reasoning
                         print(f"RESPONSE DONE FULL DUMP: {json.dumps(response, indent=2)}")

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
                "threshold": 0.6, # Increased sensitivity threshold to avoid echo/noise
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500
            },
# ... (rest of file)
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
