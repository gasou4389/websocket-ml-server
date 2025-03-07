from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json

app = FastAPI()

# Store connected clients
clients = []

# Store latest predictions (in-memory for now)
predictions = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        clients.remove(websocket)

async def send_updates():
    while True:
        if predictions:
            data = json.dumps(predictions)
            for client in clients:
                await client.send_text(data)
        await asyncio.sleep(5)  # Send updates every 5 seconds

@app.post("/update_predictions")
async def update_predictions(data: dict):
    global predictions
    predictions = data  # Store new predictions
    return {"message": "Predictions updated"}

# Run the update loop
asyncio.create_task(send_updates())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
