import logging
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request

app = FastAPI()
clients = {}  # Stores WebSocket connections

@app.websocket("/games")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections and ensures correct JSON formatting."""
    await websocket.accept()
    logging.info(f"✅ WebSocket Connection Opened: {websocket.client}")

    try:
        while True:
            try:
                message = await websocket.receive_text()
                logging.info(f"📩 Received from client: {message}")

                # ✅ Ensure we send only raw JSON (remove "Server Echo: ")
                await websocket.send_text(message)  
            except WebSocketDisconnect:
                logging.warning(f"❌ Client Disconnected: {websocket.client}")
                clients.pop(websocket, None)
                break
    except Exception as e:
        logging.error(f"❌ WebSocket Error: {e}")




@app.post("/forward_data")
async def forward_data(request: Request):
    """Receives predictions and forwards ALL data to WebSocket clients."""
    try:
        data = await request.json()
        predictions = data.get("predictions", [])

        if clients:
            json_data = json.dumps(predictions)
            logging.info(f"✅ Forwarding {len(predictions)} records to {len(clients)} WebSocket clients")

            for websocket in list(clients.keys()):
                try:
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_text(json_data)
                        logging.info(f"📤 Sent to {websocket.client}")
                    else:
                        logging.warning(f"⚠ WebSocket {websocket.client} closed before sending data.")
                        clients.pop(websocket, None)
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.pop(websocket, None)

        return {"message": "Data forwarded to WebSocket"}
    except Exception as e:
        logging.error(f"❌ Error in forward_data: {e}")
        return {"error": f"Failed to forward data: {e}"}






