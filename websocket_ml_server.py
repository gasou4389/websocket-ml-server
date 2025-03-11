from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
import json
import logging
import asyncio
import aiohttp
import os

app = FastAPI()

# ✅ Replace with your actual Ngrok URL
NGROK_URL = "https://990a-2600-1700-fc5-27c0-c8de-b237-9864-d523.ngrok-free.app/receive_full_data"

clients = {}  # Store WebSocket clients

async def fetch_predictions_from_ngrok():
    """Fetches full predictions.json from Ngrok API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(NGROK_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    logging.info(f"📥 Received {len(data)} records from Ngrok")
                    return data
                else:
                    logging.warning(f"⚠ Ngrok API request failed: {response.status}")
                    return []
    except Exception as e:
        logging.error(f"❌ Error fetching from Ngrok: {e}")
        return []

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
            clients[websocket] = None  # Subscribe to all games

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

async def send_live_nba_data():
    """Continuously fetches and sends latest predictions to WebSocket clients."""
    while True:
        if clients:
            predictions = await fetch_predictions_from_ngrok()  # ✅ Get latest data

            for websocket, game_id in list(clients.items()):
                try:
                    filtered_data = [p for p in predictions if game_id is None or p.get("game_ID") == game_id]
                    json_data = json.dumps(filtered_data)

                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_text(json_data)
                        logging.info(f"✅ Sent {len(filtered_data)} records to WebSocket client {websocket.client}")
                    else:
                        logging.warning(f"⚠ WebSocket {websocket.client} closed before sending data.")
                        clients.pop(websocket, None)
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.pop(websocket, None)

        await asyncio.sleep(10)  # ✅ Send updates every 10 seconds

@app.on_event("startup")
async def startup_event():
    """Starts the background task to send WebSocket data."""
    asyncio.create_task(send_live_nba_data())

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)



