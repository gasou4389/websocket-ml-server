import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request

app = FastAPI()
clients = set()
latest_predictions = []  # Stores latest predictions

@app.websocket("/games")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections and sends valid JSON."""
    await websocket.accept()
    logging.info(f"✅ WebSocket Connection Opened: {websocket.client}")

    try:
        while True:
            message = await websocket.receive_text()
            logging.info(f"📩 Received: {message}")

            request_data = json.loads(message)
            if request_data.get("request") == "all_games":
                response_json = json.dumps(latest_predictions, ensure_ascii=False)
                await websocket.send_text(response_json)
                logging.info(f"✅ Sent {len(latest_predictions)} games to WebSocket client")
    except WebSocketDisconnect:
        logging.warning(f"❌ Client Disconnected: {websocket.client}")
        clients.remove(websocket)

@app.post("/forward_data")
async def forward_data(request: Request):
    """Receives predictions and forwards ALL data to WebSocket clients."""
    global latest_predictions
    try:
        data = await request.json()
        latest_predictions = data.get("predictions", [])  # ✅ Store latest data

        if clients:
            json_data = json.dumps(latest_predictions)
            logging.info(f"✅ Forwarding {len(latest_predictions)} records to {len(clients)} WebSocket clients")

            for websocket in list(clients):
                try:
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_text(json_data)
                        logging.info(f"📤 Sent to {websocket.client}")
                    else:
                        logging.warning(f"⚠ WebSocket {websocket.client} closed before sending data.")
                        clients.remove(websocket)
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.remove(websocket)

        return {"message": "Data forwarded to WebSocket"}
    except Exception as e:
        logging.error(f"❌ Error in forward_data: {e}")
        return {"error": f"Failed to forward data: {e}"}