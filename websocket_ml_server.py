from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
import json
import logging
import asyncio

app = FastAPI()

clients = {}  # Store WebSocket clients

@app.websocket("/games")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections, filtering by game_id."""
    await websocket.accept()
    logging.info(f"✅ WebSocket Connection Opened: {websocket.client}")

    try:
        data = await websocket.receive_text()
        request_data = json.loads(data)
        game_id = request_data.get("game_id")
        
        if game_id:
            logging.info(f"🎯 Client subscribed to game_id: {game_id}")
            clients[websocket] = game_id
        else:
            clients[websocket] = None

        while True:
            try:
                message = await websocket.receive_text()
                logging.info(f"📩 Received from client: {message}")
            except WebSocketDisconnect:
                logging.warning(f"❌ Client Disconnected: {websocket.client}")
                clients.pop(websocket, None)
                break

    except WebSocketDisconnect:
        logging.warning(f"❌ Client Disconnected: {websocket.client}")
        clients.pop(websocket, None)

@app.post("/forward_data")
async def forward_data(request: Request):
    """Receives predictions from Flask and forwards to WebSocket clients."""
    try:
        data = await request.json()
        predictions = data.get("predictions", [])

        if clients:
            for websocket, game_id in list(clients.items()):
                try:
                    filtered_data = [p for p in predictions if game_id is None or p.get("game_ID") == game_id]
                    json_data = json.dumps(filtered_data)

                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_text(json_data)
                        logging.info(f"✅ Sent {len(filtered_data)} records to WebSocket client")
                    else:
                        logging.warning(f"⚠ WebSocket {websocket.client} closed before sending data.")
                        clients.pop(websocket, None)
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.pop(websocket, None)

        return {"message": "Data forwarded to WebSocket"}
    except Exception as e:
        return {"error": f"Failed to forward data: {e}"}


