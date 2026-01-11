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
    while True:
            # 1. Receive the raw bytes
            raw_data = await websocket.receive_bytes()
            
            # 2. Decode and parse to a dictionary
            clean_str = raw_data.decode("utf-8").rstrip('\x00')
            try:
                msg_dict = json.loads(clean_str)
                
                # 3. FORCE the sender ID to be the correct one (Base 0)
                # We use players.index(websocket) to get the actual position (0, 1, or 2)
                msg_dict["sender"] = players.index(websocket)
                
                # 4. Turn it back into bytes to send
                out_packet = json.dumps(msg_dict).encode("utf-8")
                
                for player in players:
                    await player.send_bytes(out_packet)
                    
            except Exception as e:
                print(f"Error parsing JSON: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
