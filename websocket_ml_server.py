import os
import json
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# ✅ Set the correct path to your JSON file
LOCAL_JSON_PATH = "C:\\NBA\\predictions.json"



logging.basicConfig(level=logging.DEBUG)
clients = {}  # Store connected clients

def load_predictions():
    """Load predictions from the local JSON file."""
    try:
        if not os.path.exists(LOCAL_JSON_PATH):
            logging.error(f"❌ Missing predictions file: {LOCAL_JSON_PATH}")
            return []

        with open(LOCAL_JSON_PATH, "r", encoding="utf-8") as file:
            predictions = json.load(file)
            logging.debug(f"✅ Predictions JSON loaded: {json.dumps(predictions, indent=2)}")  # ✅ Print full JSON data
            return predictions
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"❌ Error loading predictions JSON: {e}")
        return []


async def send_live_nba_data():
    """Continuously reads local JSON and sends updates to WebSocket clients."""
    while True:
        if clients:
            logging.debug("🔥 Fetching latest predictions from local file...")
            predictions = load_predictions()  # ✅ Read from local file

            for websocket, game_id in list(clients.items()):
                try:
                    # ✅ Filter predictions for the specific game_id
                    filtered_data = [pred for pred in predictions if pred.get("game_ID") == game_id]

                    json_data = json.dumps(filtered_data)
                    logging.debug(f"📤 Sending {len(filtered_data)} records to client {websocket.client}")

                    await websocket.send_text(json_data)
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.pop(websocket, None)

        await asyncio.sleep(5)  # ✅ Check for new updates every 5 seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 WebSocket Server Starting...")
    asyncio.create_task(send_live_nba_data())  # ✅ Start the background task
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
            logging.warning("⚠ No game_id provided by client")

        while True:
            await asyncio.sleep(60)

    except WebSocketDisconnect:
        logging.info(f"❌ Client Disconnected: {websocket.client}")
        clients.pop(websocket, None)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))


















