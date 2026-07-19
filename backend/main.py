from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="Disaster Relief System")


active_connections: list[WebSocket] = []

@app.get("/")
async def root():
    return {"status": "Disaster Relief System backend running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)