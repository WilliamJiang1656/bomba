import os
import uvicorn
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# Just a list to keep track of everyone's connection
players = []

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_friends.append(websocket)
    
    player_id = len(players)
    print(f"Player {player_id} joined the lobby!")

    try:
        while True:
            # Receive whatever JSON data your GameMaker sends
            data = await websocket.receive_bytes()
            
            # THE RELAY: Loop through every connected friend and send them the data
            for player in players:
                # We send it to everyone (even the sender, so they get confirmation)
                await player.send_bytes(data)
                
    except WebSocketDisconnect:
        players.remove(websocket)
        print(f"A player disconnected.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
