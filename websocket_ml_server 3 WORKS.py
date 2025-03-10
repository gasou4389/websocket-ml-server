import os
import json
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# ✅ Automatically adjust the path for different environments
if os.getenv("RAILWAY_ENVIRONMENT"):  # Detect if running on Railway
    json_file_path = "/app/predictions.json"  # Adjust for Linux deployment
else:
    json_file_path = r"C:\NBA\predictions.json"  # Local Windows path

logging.basicConfig(level=logging.DEBUG)
clients = set()

def load_predictions():
    """Load predictions from JSON file and ensure each row has a unique Row_ID."""
    try:
        logging.debug(f"🔍 Checking for predictions JSON at: {json_file_path}")
        with open(json_file_path, "r", encoding="utf-8") as f:
            predictions = json.load(f)
            logging.debug("✅ Predictions JSON loaded successfully.")

        # ✅ Ensure each entry has a unique identifier
        for pred in predictions:
            if "Row_ID" not in pred:
                pred["Row_ID"] = f"{pred.get('game_ID', 'unknown')}_{pred.get('Row', 'unknown')}"

        return predictions  # ✅ Return correctly processed data
    except FileNotFoundError:
        logging.error("❌ Predictions JSON file not found. Ensure it's deployed correctly.")
        return []
    except json.JSONDecodeError:
        logging.error("❌ JSON decoding error: File might be corrupted.")
        return []

async def send_live_nba_data():
    """Continuously sends the latest NBA predictions to connected WebSocket clients."""
    while True:
        if clients:
            logging.debug(f"🔥 Fetching latest predictions from JSON...")
            predictions = load_predictions()

            if not predictions:
                logging.warning("⚠ No predictions available to send.")
            else:
                json_data = json.dumps(predictions)

                # ✅ DEBUG: Print the data before sending
                logging.debug(f"📤 Sending data to {len(clients)} clients: {json_data}")

                for client in list(clients):
                    try:
                        await client.send_text(json_data)
                    except Exception as e:
                        logging.error(f"❌ Failed to send data: {e}")
                        clients.remove(client)

        await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown."""
    logging.info("🚀 WebSocket Server Starting...")
    asyncio.create_task(send_live_nba_data())  # ✅ Ensure background task starts
    yield
    logging.info("🛑 WebSocket Server Stopping...")

app = FastAPI(lifespan=lifespan)

# ✅ Allow WebSocket connections & CORS (Fix for 403 Forbidden error)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend domain for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections and disconnections."""
    await websocket.accept()
    clients.add(websocket)
    logging.info(f"✅ WebSocket Connection Opened: {websocket.client}")

    try:
        while True:
            data = await websocket.receive_text()
            logging.debug(f"📩 Received from client: {data}")
    except WebSocketDisconnect:
        logging.info(f"❌ Client Disconnected: {websocket.client}")
        clients.remove(websocket)  # ✅ Ensure client removal

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))












