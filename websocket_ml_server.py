import os
import json
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
import aiohttp

# ✅ Determine whether running on Railway or locally
if os.getenv("RAILWAY_ENVIRONMENT"):
    LOCAL_JSON_PATH = "/app/predictions.json"  # ❌ This file won't exist
else:
    LOCAL_JSON_PATH = "C:\\NBA\\predictions.json"  # ✅ Local Windows path

async def fetch_predictions_from_local():
    """Fetches full predictions.json from local Flask API."""
    url = "https://fffb-2600-1700-fc5-27c0-d4fb-eacc-e925-d274.ngrok-free.app"  # ✅ Local server URL

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logging.debug(f"📥 Received {len(data)} records from local API")
                    return data
                else:
                    logging.warning(f"⚠ Local API request failed: {response.status}")
                    return []
    except Exception as e:
        logging.error(f"❌ Error fetching from local API: {e}")
        return []

logging.basicConfig(level=logging.DEBUG)
clients = {}  # Store connected clients

async def send_live_nba_data():
    """Continuously sends latest predictions to WebSocket clients."""
    while True:
        if clients:
            predictions = await fetch_predictions_from_local()  # ✅ Get latest data

            for websocket, game_id in list(clients.items()):
                try:
                    filtered_data = [pred for pred in predictions if pred.get("game_ID") == game_id]
                    json_data = json.dumps(filtered_data)

                    if filtered_data:
                        logging.debug(f"📤 Sending {len(filtered_data)} records to {websocket.client}")
                        await websocket.send_text(json_data)
                    else:
                        logging.warning(f"⚠ No matching data for game_id {game_id}")
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.pop(websocket, None)

        await asyncio.sleep(10)  # ✅ Send updates every 10 seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown tasks."""
    logging.info("🚀 WebSocket Server Starting...")

    if not os.getenv("RAILWAY_ENVIRONMENT"):  # ✅ Only send updates when running locally
        asyncio.create_task(send_live_nba_data())

    yield
    logging.info("🛑 WebSocket Server Stopping...")

app = FastAPI(lifespan=lifespan)

# ✅ Allow CORS for WebSockets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Allow all origins (For testing, later restrict to Wix domain)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/games")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections, filtering by game_id."""
    await websocket.accept()
    logging.info(f"✅ WebSocket Connection Opened: {websocket.client}")

    try:
        data = await websocket.receive_text()
        request_data = json.loads(data)
        game_id = request_data.get("game_id")
        full_file_request = request_data.get("full_file", False)  # ✅ New flag

        if game_id:
            logging.info(f"🎯 Client subscribed to game_id: {game_id}")
            clients[websocket] = game_id
        else:
            logging.warning("⚠ No game_id provided by client, defaulting to all games")
            clients[websocket] = None  # Allow clients to receive all game updates

        logging.info("📤 Sending latest available data to new client...")

        # ✅ Fetch predictions (Different sources for local vs Railway)
        if os.getenv("RAILWAY_ENVIRONMENT"):  # ✅ Running on Railway
            logging.info("🚀 Requesting full data from local machine")
            predictions = await fetch_predictions_from_local()  # ✅ Correct function
        else:
            predictions = await fetch_predictions_from_local()  # ✅ Local load

        # ✅ Handle full file requests
        if full_file_request:
            filtered_data = predictions  # ✅ Return full dataset
        else:
            filtered_data = [pred for pred in predictions if game_id is None or pred.get("game_ID") == game_id]

        # ✅ Always send data immediately upon connection
        await websocket.send_text(json.dumps(filtered_data))
        logging.info(f"✅ Sent {len(filtered_data)} records!")

        while True:
            try:
                message = await websocket.receive_text()  # Keep connection open
                logging.info(f"📩 Received from client: {message}")
            except WebSocketDisconnect:
                logging.warning(f"❌ Client Disconnected: {websocket.client}")
                clients.pop(websocket, None)
                break  # Exit loop if disconnected

    except WebSocketDisconnect:
        logging.info(f"❌ Client Disconnected: {websocket.client}")
        clients.pop(websocket, None)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

