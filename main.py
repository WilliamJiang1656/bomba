from fastapi import FastAPI, WebSocket

app = FastAPI()

# test route for HTTP
@app.get("/")
def root():
    print("Root hit", flush=True)
    return {"status": "Daijoubu"}

# WebSocket for GameMaker
@app.websocket("/")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()  # accept connection
    await ws.send_text("connected among us")  # confirm connection
    print("Player connected cracked", flush=True)

    players = []

    players.append(ws)
    try:
        while True:
            data = await ws.receive_text()  # wait for message
            print("Received:", data, flush=True)
            # broadcast to all players
            for p in players:
                await p.send_text(data)
    except:
        players.remove(ws)
        print("Player disconnected rip", flush=True)
