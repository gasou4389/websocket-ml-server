import asyncio
import logging
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from contextlib import asynccontextmanager
import json  # ✅ Add this import

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

clients = set()



async def send_live_nba_data():
    while True:
        if clients:
            logging.debug("🔥 Sending NBA data...")
            sample_data = [
                {"game_id": "LAL_vs_BOS", "total": 220.5, "over": "54.2%", "under": "45.8%"},
                {"game_id": "MIA_vs_NYK", "total": 216.5, "over": "43.6%", "under": "56.4%"}
            ]
            json_data = json.dumps(sample_data)  # ✅ Convert to valid JSON
            for client in list(clients):
                try:
                    await client.send_text(json_data)  # ✅ Send properly formatted JSON
                except Exception as e:
                    logging.error(f"❌ Failed to send data: {e}")
                    clients.remove(client)
        await asyncio.sleep(10)  # Keep the loop alive


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
            logging.debug(f"📩 Received: {data}")
    except WebSocketDisconnect:
        logging.info(f"❌ Client Disconnected: {websocket.client}")
        clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    print("🚀 WebSocket Server Starting...")
    uvicorn.run(app, host="0.0.0.0", port=8080)






