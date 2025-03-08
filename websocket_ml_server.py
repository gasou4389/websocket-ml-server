import json
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from contextlib import asynccontextmanager
import os 

# ✅ Import function to fetch predictions dynamically
from process_predictions import get_structured_predictions  

logging.basicConfig(level=logging.DEBUG)

clients = set()

async def send_live_nba_data():
    while True:
        if clients:
            logging.debug("🔥 Fetching latest predictions from Excel...")

            # ✅ Call the function to get updated predictions
            structured_predictions = get_structured_predictions()

            # ✅ Convert to JSON and send to clients
            json_data = json.dumps(structured_predictions)  
            for client in list(clients):
                try:
                    await client.send_text(json_data)
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.remove(client)

        await asyncio.sleep(10)  # Adjust frequency based on how often data updates

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 WebSocket Server Starting...")
    asyncio.create_task(send_live_nba_data())  # ✅ Start sending predictions
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








