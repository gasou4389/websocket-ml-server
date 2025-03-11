import logging
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request

app = FastAPI()
clients = {}  # Stores WebSocket connections

@app.websocket("/games")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections."""
    await websocket.accept()
    logging.info(f"✅ WebSocket Connection Opened: {websocket.client}")

    clients[websocket] = True  # ✅ Store client

    try:
        while True:
            message = await websocket.receive_text()
            logging.info(f"📩 Received from client: {message}")
    except WebSocketDisconnect:
        logging.warning(f"❌ Client Disconnected: {websocket.client}")
        if websocket in clients:
            del clients[websocket]


@app.post("/forward_data")
async def forward_data(request: Request):
    """Receives predictions and forwards them to WebSocket clients."""
    try:
        data = await request.json()
        predictions = data.get("predictions", [])
        
        logging.info(f"Received data: {json.dumps(predictions, indent=2)}")

        if clients:
            json_data = json.dumps(predictions)
            for websocket in list(clients.keys()):
                try:
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_text(json_data)
                        logging.info(f"✅ Sent {len(predictions)} records to WebSocket client")
                    else:
                        logging.warning(f"⚠ WebSocket {websocket.client} closed before sending data.")
                        clients.pop(websocket, None)
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.pop(websocket, None)

        return {"message": "Data forwarded to WebSocket"}
    except Exception as e:
        return {"error": f"Failed to forward data: {e}"}





