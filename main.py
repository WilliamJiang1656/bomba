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
    players.append(websocket)
    
    player_id = len(players)
    print(f"Player {player_id} joined the lobby!")
    
    # Send the "Welcome" packet to ONLY this new player
    welcome_data = {
        "header": "WELCOME",
        "assigned_id": player_id
    }
    # We use send_text here, but GameMaker will read it via the buffer
    await websocket.send_text(json.dumps(welcome_data))
    
    print(f"Player {player_id} connected and received their ID.")
    try:
        while True:
            data = await websocket.receive_bytes()
        
            # Strip the null terminator \x00 if it exists
            clean_data = data.decode("utf-8").rstrip('\x00')
        
            # Relay the clean data to everyone
            for player in players:
                    await player.send_bytes(clean_data.encode("utf-8"))
                
    except WebSocketDisconnect:
        players.remove(websocket)
        print(f"A player disconnected.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
