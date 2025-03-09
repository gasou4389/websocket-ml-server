import os
import json
import asyncio
import logging
import requests  # ✅ NEW: Use requests to get fresh JSON from Waitress
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# ✅ Waitress HTTP Server URL for JSON
WAITRESS_JSON_URL = "http://127.0.0.1:5000/predictions.json"

logging.basicConfig(level=logging.DEBUG)
clients = {}  # ✅ Store clients with their requested `game_id`

def load_predictions():
    """Fetch the latest predictions from Waitress HTTP Server instead of reading from file."""
    try:
        logging.debug(f"🔍 Fetching predictions from: {WAITRESS_JSON_URL}")
        response = requests.get(WAITRESS_JSON_URL)

        if response.status_code == 200:
            predictions = response.json()
            logging.debug("✅ Predictions JSON loaded successfully.")

            # ✅ Ensure each entry has a unique Row_ID
            for pred in predictions:
                if "Row_ID" not in pred:
                    pred["Row_ID"] = f"{pred.get('game_ID', 'unknown')}_{pred.get('Row', 'unknown')}"

            return predictions
        else:
            logging.error(f"❌ Failed to fetch predictions (HTTP {response.status_code})")
            return []
    except requests.RequestException as e:
        logging.error(f"❌ Error fetching JSON from Waitress: {e}")
        return []

def get_unique_games():
    """Extract unique games from the predictions JSON (ALWAYS FORCE RELOAD)."""
    predictions = load_predictions()  # ✅ Always get fresh data
    unique_games = {}

    for pred in predictions:
        game_id = pred.get("game_ID", "unknown")
        game_name = pred.get("game_name", f"Game {game_id}")

        if game_id not in unique_games:
            unique_games[game_id] = game_name

    return [{"game_ID": gid, "game_name": gname} for gid, gname in unique_games.items()]

async def send_live_nba_data():
    """Continuously sends filtered NBA predictions to clients."""
    while True:
        if clients:
            logging.debug("🔥 Fetching latest predictions from Waitress...")
            predictions = load_predictions()  # ✅ Always reload JSON

            for websocket, game_id in list(clients.items()):
                try:
                    filtered_data = [pred for pred in predictions if pred.get("game_ID") == game_id]

                    if not filtered_data:
                        logging.warning(f"⚠ No predictions found for game_id: {game_id}")

                    json_data = json.dumps(filtered_data)
                    logging.debug(f"📤 Sending {len(filtered_data)} records to client {websocket.client}")

                    await websocket.send_text(json_data)
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.pop(websocket, None)

        await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 WebSocket Server Starting...")
    asyncio.create_task(send_live_nba_data())
    yield
    logging.info("🛑 WebSocket Server Stopping...")

app = FastAPI(lifespan=lifespan)

# ✅ Allow WebSocket & CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections, filtering by game_id (ALWAYS RELOADS JSON)."""
    await websocket.accept()
    logging.info(f"✅ WebSocket Connection Opened: {websocket.client}")

    try:
        data = await websocket.receive_text()
        game_id = json.loads(data).get("game_id")

        if game_id:
            logging.info(f"🎯 Client subscribed to game_id: {game_id}")
            clients[websocket] = game_id
        else:
            logging.warning("⚠ No game_id provided by client")

        while True:
            await asyncio.sleep(60)

    except WebSocketDisconnect:
        logging.info(f"❌ Client Disconnected: {websocket.client}")
        clients.pop(websocket, None)

@app.websocket("/games")
async def websocket_games(websocket: WebSocket):
    """Sends a list of unique game names & IDs (ALWAYS RELOADS JSON)."""
    await websocket.accept()
    try:
        games = get_unique_games()  # ✅ Always reload JSON
        await websocket.send_text(json.dumps(games))
        logging.info(f"📤 Sent {len(games)} game links to client")
    except Exception as e:
        logging.error(f"❌ Failed to send game list: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
















