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
                request_data = json.loads(message)

                # ✅ If client requests all games, send all predictions
                if request_data.get("request") == "all_games":
                    with open("C:\\NBA\\predictions.json", "r", encoding="utf-8") as file:
                        predictions = json.load(file)

                    json_data = json.dumps(predictions)
                    await websocket.send_text(json_data)
                    logging.info(f"✅ Sent {len(predictions)} games to WebSocket client")

            except WebSocketDisconnect:
                logging.warning(f"❌ Client Disconnected: {websocket.client}")
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






