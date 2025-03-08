import websockets
import asyncio

async def test_ws():
    async with websockets.connect("ws://127.0.0.1:8000/ws") as ws:
        print("Connected!")
        await ws.send("ping")  # Send a test message
        response = await ws.recv()
        print("Received:", response)

asyncio.run(test_ws())
