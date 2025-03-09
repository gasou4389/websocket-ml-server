import os
import json
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from contextlib import asynccontextmanager

# ✅ Define path to JSON file
json_file_path = "C:/NBA/predictions.json"  # ✅ Save outside OneDrive

logging.basicConfig(level=logging.DEBUG)
clients = set()

def load_predictions():
    """Load predictions from JSON file and ensure each row has a unique Row_ID."""
    try:
        with open(json_file_path, "r") as f:
            predictions = json.load(f)
        
        # ✅ Ensure each entry has a unique identifier
        for pred in predictions:
            if "Row_ID" not in pred:
                pred["Row_ID"] = f"{pred['game_ID']}_{pred['Row']}"

        return predictions
    except FileNotFoundError:
        logging.error("❌ Predictions JSON file not found.")
        return []
    except json.JSONDecodeError:
        logging.error("❌ JSON decoding error: File might be corrupted.")
        return []

async def send_live_nba_data():
    """Continuously send NBA predictions to all connected clients every 10 seconds."""
    while True:
        if clients:
            logging.debug("🔥 Fetching latest predictions from JSON...")
            structured_predictions = load_predictions()

            json_data = json.dumps(structured_predictions, indent=4)
            logging.debug(f"📤 Sending data to clients: {json_data}")

            for client in list(clients):
                try:
                    await client.send_text(json_data)
                except Exception as e:
                    logging.error(f"❌ Failed to send data to client: {e}")
                    clients.remove(client)  # Remove disconnected clients

        await asyncio.sleep(10)  # Send updates every 10 seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 WebSocket Server Starting...")
    asyncio.create_task(send_live_nba_data())
    yield
    logging.info("🛑 WebSocket Server Stopping...")

app = FastAPI(lifespan=lifespan)

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
        clients.remove(websocket)  # Ensure client removal

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))










