import asyncio
import websockets
import sys

async def test_ws(uri):
    try:
        async with websockets.connect(uri) as ws:
            print(f"✅ Connected to WebSocket at {uri}!")
            await ws.send("ping")
            response = await ws.recv()
            print("📩 Received:", response)
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    # Choose environment: local or online
    mode = sys.argv[1] if len(sys.argv) > 1 else "local"

    if mode == "local":
        ws_uri = "ws://127.0.0.1:8080/ws"  # Local WebSocket
    else:
        ws_uri = "wss://your-app.up.railway.app/ws"  # Online WebSocket (Replace with actual URL)

    asyncio.run(test_ws(ws_uri))

