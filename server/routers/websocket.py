import json
import traceback
active_websockets = {}  # Changed to dictionary to store session_id -> websocket mapping

async def send_to_websocket(session_id: str, event:dict):
    ws = active_websockets.get(session_id)
    if ws:
        try:
            await ws.send_text(json.dumps(event))
        except Exception as e:
            print(f"Error sending to websocket: {e}")
            traceback.print_exc()