from fastapi import FastAPI, WebSocket

app = FastAPI()

players = []

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
            # Broadcast to all players
            for p in players:
                await p.send_text(data)
    except:
        players.remove(ws)
        print("Player disconnected", flush=True)
