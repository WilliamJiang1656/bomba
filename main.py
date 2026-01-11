from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("GameMaker Connected!")
    try:
        while True:
            # Receive message from GameMaker
            data = await websocket.receive_text()
            print(f"Received from GM: {data}")
            
            # Send a response back
            await websocket.send_text(f"Server received your move: {data}")
    except WebSocketDisconnect:
        print("GameMaker Disconnected")
