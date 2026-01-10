from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.get("/")
def root():
    return {"status": "Daijoubu"}

players = []

@app.websocket("/")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await ws.send_text("connected 🌚")  # confirm connection

async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    players.append(ws)

    if len(players) > 5:
        await ws.send_text("Muri room full")
        await ws.close()
        return

    try:
        while True:
            data = await ws.receive_text()
            # broadcast to everyone
            for p in players:
                await p.send_text(data)

    except WebSocketDisconnect:
        players.remove(ws)
