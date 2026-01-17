import os
import uvicorn
import json
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# Only use SEATS. This keeps ID 0, 1, and 2 assigned to specific 'spots'.
seats = [
    {"socket": None, "active": False, "ready": False},
    {"socket": None, "active": False, "ready": False},
    {"socket": None, "active": False, "ready": False},
    {"socket": None, "active": False, "ready": False},
    {"socket": None, "active": False, "ready": False}
]

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # find a seat
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

    # welcome data
    welcome_data = {"header": "WELCOME", "assigned_id": assigned_id}

    payload = (json.dumps(welcome_data) + "\0").encode("utf-8")
    await websocket.send_bytes(payload)
    
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

                if msg_dict["header"] == "READY":
                    seats[assigned_id]["ready"] = msg_dict["is_ready"] # True or False
                    
                    # Check if ALL active players are ready
                    active_seats = [s for s in seats if s["active"]]
                    num_active = len(active_seats)
                    
                    # ONLY start if there are exactly 5 people AND they are all ready
                    if all(s["ready"] for s in active_seats):
                        start_packet = {"header": "START_GAME"}
                        
                        # make deck
                        deck = [] 
                        # Standard Cards
                        for val in range(13): # 0-12
                            for suit in range(4): # 0-3
                                for back in range(2): # 0-1
                                    deck.append([val, suit, back])
                        # Jokers
                        for back in range(2):
                            deck.append([13, 0, back]) # Black Joker
                            deck.append([14, 2, back]) # Red Joker
                            
                        random.shuffle(deck)

                        flip_card = deck[random.randrange(len(deck)-3)]
                        while(flip_card[0] > 9): # queen
                            flip_card = deck[random.randrange(len(deck)-3)]
                        start_packet["flip_card"] = flip_card
                        
                        #distribute
                        hands = [[] for _ in range(5)]
                        for cards in range(21): # 21 cards
                            for p in range(5): # 5 players
                                hands[p].append(deck.pop())
                        start_packet["bottom_cards"] = deck

                        # find who got flip card
                        flip_id = 0
                        for p in range(5):
                            if flip_card in hands[p]:
                                flip_id = p
                                break
                        start_packet["flip_id"] = flip_id
                        
                        
                        for p, seat in enumerate(seats):
                            if seat["active"] and seat["socket"]:
                                start_packet["hand"] = hands[p]
                                start_payload = (json.dumps(start_packet) + "\0").encode("utf-8")
                                await seat["socket"].send_bytes(start_payload)
                
                else if msg_dict["header"] == "EXIT":
                    for p in range(5):
                        seats[p]["ready"] = false

                            
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
