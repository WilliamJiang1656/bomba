from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Optional CORS for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

players = []

@app.get("/")
def root():
    print("Root endpoint hit", flush=True)
    return {"status": "Server running"}

@app.websocket("/")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("Player connected", flush=True)
    await ws.send_text("connected")

    players.append(ws)
    try:
        while True:
            data = await ws.receive_text()
            print("Received:", data, flush=True)
            # Broadcast to all connected players
            for p in players:
                await p.send_text(data)
    except:
        players.remove(ws)
        print("Player disconnected", flush=True)
