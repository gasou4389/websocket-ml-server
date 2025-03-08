import os
import json
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from contextlib import asynccontextmanager

# ✅ Define path to JSON file
json_file_path = os.path.join(os.path.dirname(__file__), "predictions.json")

logging.basicConfig(level=logging.DEBUG)
clients = set()

def load_predictions():
    """Load predictions from JSON file."""
    try:
        with open(json_file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("❌ Predictions JSON file not found.")
        return []

async def send_live_nba_data():
    while True:
        if clients:
            logging.debug("🔥 Fetching latest predictions from JSON...")
            structured_predictions = load_predictions()

            json_data = json.dumps(structured_predictions)
            logging.debug(f"📤 Sending data to clients: {json_data}")

            for client in list(clients):
                try:
                    await client.send_text(json_data)
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.remove(client)

        await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 WebSocket Server Starting...")
    asyncio.create_task(send_live_nba_data())
    yield
    logging.info("🛑 WebSocket Server Stopping...")

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    logging.info(f"✅ WebSocket Connection Opened: {websocket.client}")

    try:
        while True:
            data = await websocket.receive_text()
            logging.debug(f"📩 Received from client: {data}")
    except WebSocketDisconnect:
        logging.info(f"❌ Client Disconnected: {websocket.client}")
        clients.remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))









