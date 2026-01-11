import os
import uvicorn
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# Only use SEATS. This keeps ID 0, 1, and 2 assigned to specific 'spots'.
seats = [
    {"socket": None, "active": False},
    {"socket": None, "active": False},
    {"socket": None, "active": False},
    {"socket": None, "active": False},
    {"socket": None, "active": False}
]

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # 1. FIND A SEAT
    assigned_id = -1
    for i, seat in enumerate(seats):
        if not seat["active"]:
            assigned_id = i
            seat["socket"] = websocket
            seat["active"] = True
            break
            
    if assigned_id == -1:
        await websocket.close(code=4000)
        return

    print(f"Seat {assigned_id} taken.")

    # 2. WELCOME
    welcome_data = {"header": "WELCOME", "assigned_id": assigned_id}
    await websocket.send_text(json.dumps(welcome_data))
    
    try:
        while True:
            raw_data = await websocket.receive_bytes()
            clean_str = raw_data.decode("utf-8").rstrip('\x00')
        
            try:
                msg_dict = json.loads(clean_str)
                # Use the assigned_id we locked in at the start!
                msg_dict["sender"] = assigned_id
                final_json = (json.dumps(msg_dict) + "\0").encode("utf-8")
                
                # 3. BROADCAST only to active sockets
                for seat in seats:
                    if seat["active"] and seat["socket"]:
                        await seat["socket"].send_bytes(final_json)
                        
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        # 4. LEAVE THE SEAT OPEN FOR REJOINING
        seats[assigned_id]["active"] = False
        seats[assigned_id]["socket"] = None
        print(f"Seat {assigned_id} is now vacant (Player disconnected).")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
