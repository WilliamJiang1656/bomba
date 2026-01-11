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
            # Change this from receive_text() to receive_bytes()
            data = await websocket.receive_bytes()
            
            # Convert the bytes back to a string so we can read it
            message_text = data.decode("utf-8")
            print(f"Binary Message received: {message_text}")
            
            # Send an echo back as text
            await websocket.send_text(f"Echo: {message_text}")
            
    except WebSocketDisconnect:
        print("GameMaker Disconnected")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
