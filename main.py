import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# This helps prevent Railway from rejecting the connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "online", "message": "Bomba Server is Running"}

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("GameMaker Connected via WebSocket!")
    try:
        while True:
            # Receive text from GameMaker
            data = await websocket.receive_text()
            print(f"Message received: {data}")
            
            # Send it back to confirm
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("GameMaker Disconnected")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
