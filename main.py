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
            # 1. Wait for bytes from GameMaker
            raw_data = await websocket.receive_bytes()
        
            # 2. Decode bytes to string
            clean_str = raw_data.decode("utf-8").rstrip('\x00')
        
            # --- INTERNAL TRY: PROTECT THE JSON PARSING ---
            try:
                # 3. Convert string to a dictionary
                msg_dict = json.loads(clean_str)
                
                # 4. STAMP the sender ID (using the player's index in our list)
                # This ensures Player 1 is always ID 0, Player 2 is ID 1, etc.
                msg_dict["sender"] = players.index(websocket)
                
                # 5. Convert back to string
                final_json = json.dumps(msg_dict)
                
                # 6. Broadcast to all connected players
                for player in players:
                    # We send as bytes so GameMaker can read it into a buffer
                    await player.send_bytes(final_json.encode("utf-8"))
                    
            except json.JSONDecodeError:
                print(f"Ignored a bad packet from Player {players.index(websocket)}")
            # --- END INTERNAL TRY ---

    except WebSocketDisconnect:
        # Handle player leaving
        player_idx = players.index(websocket)
        players.remove(websocket)
        print(f"Player {player_idx} disconnected.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
