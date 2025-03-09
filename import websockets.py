import websockets
import asyncio
import json

async def test_websocket():
    uri = "wss://websocket-ml-server-production.up.railway.app/games"
    async with websockets.connect(uri) as websocket:
        response = await websocket.recv()
        print("📩 Response from /games WebSocket:", json.loads(response))

asyncio.run(test_websocket())
