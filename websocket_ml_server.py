import os
import json
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# ✅ Determine whether running on Railway or locally
if os.getenv("RAILWAY_ENVIRONMENT"):
    LOCAL_JSON_PATH = "/app/predictions.json"  # ❌ This file won't exist
else:
    LOCAL_JSON_PATH = "C:\\NBA\\predictions.json"  # ✅ Local Windows path

logging.basicConfig(level=logging.DEBUG)
clients = {}  # Store connected clients

# ✅ Ensure we don't check for file updates if it doesn't exist
last_modified = 0 if not os.path.exists(LOCAL_JSON_PATH) else os.path.getmtime(LOCAL_JSON_PATH)

def has_file_updated():
    """Check if predictions.json has been modified (Only on local machine)."""
    global last_modified

    if not os.path.exists(LOCAL_JSON_PATH):
        return False  # ✅ Don't crash if file is missing

    try:
        new_time = os.path.getmtime(LOCAL_JSON_PATH)
        if new_time > last_modified:
            last_modified = new_time
            return True
    except FileNotFoundError:
        logging.warning("⚠ predictions.json file not found!")
        return False

    return False

def load_predictions():
    """Force reload of the latest JSON data."""
    if not os.path.exists(LOCAL_JSON_PATH):
        logging.warning("⚠ File missing, returning empty list.")
        return []

    try:
        with open(LOCAL_JSON_PATH, "r", encoding="utf-8") as file:
            return json.loads(file.read())  # ✅ Ensures fresh data every time
    except Exception as e:
        logging.error(f"❌ Error loading predictions: {e}")
        return []

async def send_live_nba_data():
    """Continuously sends updates when predictions.json is modified (Only runs locally)."""
    predictions = load_predictions()  # ✅ Load initial data

    while True:
        if clients and os.path.exists(LOCAL_JSON_PATH):  # ✅ Only check file updates if it exists
            if has_file_updated():
                logging.debug("🔥 File updated! Reloading predictions...")
                predictions = load_predictions()

            for websocket, game_id in list(clients.items()):
                try:
                    filtered_data = [pred for pred in predictions if game_id is None or pred.get("game_ID") == game_id]
                    json_data = json.dumps(filtered_data)

                    if filtered_data:
                        logging.debug(f"📤 Sending {len(filtered_data)} records to client {websocket.client}")

                        # ✅ Ensure WebSocket connection is still open before sending
                        if websocket.client_state.name == "CONNECTED":
                            await websocket.send_text(json_data)
                        else:
                            logging.warning(f"⚠ WebSocket {websocket.client} closed before sending data.")
                            clients.pop(websocket, None)  # ✅ Remove disconnected client
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.pop(websocket, None)  # ✅ Handle disconnected clients properly
        await asyncio.sleep(10)  # ✅ Check for updates every 10 seconds

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
        game_id = json.loads(data).get("game_id")

        if game_id:
            logging.info(f"🎯 Client subscribed to game_id: {game_id}")
            clients[websocket] = game_id
        else:
            logging.warning("⚠ No game_id provided by client, defaulting to all games")
            clients[websocket] = None  # Allow clients to receive all game updates

        while True:
            await asyncio.sleep(60)  # Keep connection open

    except WebSocketDisconnect:
        logging.info(f"❌ Client Disconnected: {websocket.client}")
        clients.pop(websocket, None)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))






















