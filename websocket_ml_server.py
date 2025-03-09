import os
import json
import asyncio
import logging
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from http.server import SimpleHTTPRequestHandler
import threading
from socketserver import TCPServer

# ✅ Automatically get the latest JSON file
LOCAL_MACHINE_IP = "192.168.1.100"  # Replace with your actual IP
LOCAL_PORT = 5000  # The HTTP server port
json_url = f"http://{LOCAL_MACHINE_IP}:{LOCAL_PORT}/predictions.json"

if os.getenv("RAILWAY_ENVIRONMENT"):
    try:
        logging.info(f"🌍 Fetching latest JSON from {json_url}")
        response = requests.get(json_url)
        if response.status_code == 200:
            predictions = response.json()  # ✅ Fetch latest JSON from local machine
            json_file_path = None  # ✅ No need for a local file
        else:
            logging.warning(f"⚠️ Failed to fetch from local machine, using backup.")
            json_file_path = "/app/predictions.json"  # Fallback to older file
    except Exception as e:
        logging.error(f"❌ Error fetching JSON: {e}")
        json_file_path = "/app/predictions.json"  # Use fallback
else:
    json_file_path = r"C:\NBA\predictions.json"  # ✅ Use local file when not on Railway


# ✅ Start an HTTP server to serve `predictions.json`
class MyHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler to serve JSON files"""
    def do_GET(self):
        if self.path == "/predictions.json":
            try:
                with open(json_file_path, "r", encoding="utf-8") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(f.read().encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Error loading JSON: {e}".encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def start_http_server():
    """Runs the HTTP server in a separate thread."""
    with TCPServer(("", LOCAL_PORT), MyHandler) as httpd:
        logging.info(f"✅ HTTP Server Running on Port {LOCAL_PORT}")
        httpd.serve_forever()


# ✅ Start HTTP Server in a separate thread
http_thread = threading.Thread(target=start_http_server, daemon=True)
http_thread.start()


# ✅ WebSocket server logic below
clients = {}  # Store clients with their requested `game_id`

def load_predictions():
    """Always load the latest predictions JSON file from disk."""
    try:
        logging.debug(f"🔍 Checking for predictions JSON at: {json_file_path}")
        with open(json_file_path, "r", encoding="utf-8") as f:
            predictions = json.load(f)
            logging.debug("✅ Predictions JSON loaded successfully.")

        # ✅ Ensure each entry has a unique Row_ID
        for pred in predictions:
            if "Row_ID" not in pred:
                pred["Row_ID"] = f"{pred.get('game_ID', 'unknown')}_{pred.get('Row', 'unknown')}"

        return predictions
    except FileNotFoundError:
        logging.error("❌ Predictions JSON file not found.")
        return []
    except json.JSONDecodeError:
        logging.error("❌ JSON decoding error: File might be corrupted.")
        return []

async def send_live_nba_data():
    """Continuously sends filtered NBA predictions to clients."""
    while True:
        if clients:
            logging.debug("🔥 Fetching latest predictions...")
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
    """Handles WebSocket connections, filtering by game_id (FORCES JSON RELOAD)."""
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
    """Sends a list of unique game names & IDs (FORCE JSON RELOAD)."""
    await websocket.accept()
    try:
        games = load_predictions()
        unique_games = {}

        for game in games:
            game_id = game.get("game_ID", "unknown")
            game_name = game.get("game_name", f"Game {game_id}")

            if game_id not in unique_games:
                unique_games[game_id] = game_name

        game_list = [{"game_ID": gid, "game_name": gname} for gid, gname in unique_games.items()]
        await websocket.send_text(json.dumps(game_list))
        logging.info(f"📤 Sent {len(game_list)} game links to client")
    except Exception as e:
        logging.error(f"❌ Failed to send game list: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))















