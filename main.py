import os
import uvicorn
import json
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

seats = [
    {"socket": None, "active": False, "ready": False},
    {"socket": None, "active": False, "ready": False},
    {"socket": None, "active": False, "ready": False},
    {"socket": None, "active": False, "ready": False},
    {"socket": None, "active": False, "ready": False}
]

# server variables to keep track
hands = [[] for _ in range(5)]
hand_groups = [[] for _ in range(5)]
landlord_id = []
turn_id = -1
last_play_id = -1
played_cards = []
table_combo = [0 for _ in range(4)]
exit_order = []
landlord_points = 0
peasant_points = 0
bottom_cards = []
landlord_phase = False
teammate_card = []
pfp = [None for _ in range(4)]
start = False

def skip_exited(val):
    val = (val + 1) % 5
    while val in exit_order:
        val = (val + 1) % 5
    return val

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    global hands, hand_groups, landlord_id, turn_id, last_play_id, played_cards, table_combo, exit_order, landlord_points, peasant_points, bottom_cards, landlord_phase, teammate_card, pfp, start
    
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
    welcome_data = {"header": "WELCOME", "assigned_id": assigned_id, "start": start}

    payload = (json.dumps(welcome_data) + "\0").encode("utf-8")
    await websocket.send_bytes(payload)

    # if to send game data if a game is starting
    if start:
        rejoin_data = {"header": "REJOIN"}
        rejoin_data["hand"] = hands[assigned_id]
        rejoin_data["hand_groups"] = hand_groups[assigned_id]
        rejoin_data["landlord"] = landlord_id
        rejoin_data["turn"] = turn_id
        rejoin_data["last_play_id"] = last_play_id
        rejoin_data["played_cards"] = played_cards
        rejoin_data["combo"] = table_combo
        rejoin_data["exit_order"] = exit_order
        rejoin_data["landlord_points"] = landlord_points
        rejoin_data["peasant_points"] = peasant_points
        rejoin_data["bottom_cards"] = bottom_cards
        rejoin_data["landlord_phase"] = landlord_phase
        rejoin_data["teammate_card"] = teammate_card
        rejoin_data["pfp"] = pfp

        
        payload = (json.dumps(rejoin_data) + "\0").encode("utf-8")
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
                
                # broadcast to active sockets
                for s_id, seat in enumerate(seats):
                    if seat["active"] and seat["socket"]:
                        try:
                            await seat["socket"].send_bytes(final_json)
                        except (WebSocketDisconnect, RuntimeError):
                            seat["active"] = False
                            seat["socket"] = None
                            print(f"Seat {s_id} connection lost during broadcast.")

                if msg_dict["header"] == "READY":
                    seats[assigned_id]["ready"] = msg_dict["is_ready"] # True or False
                    
                    # Check if ALL active players are ready
                    active_seats = [s for s in seats if s["active"]]
                    num_active = len(active_seats)
                    
                    # ONLY start if there are exactly 5 people AND they are all ready
                    if num_active == 5 and all(s["ready"] for s in active_seats):
                        start_packet = {"header": "START_GAME"}

                        # reset vars
                        hands = [[] for _ in range(5)]
                        hand_groups = [[] for _ in range(5)]
                        landlord_id = []
                        #turn_id = -1 set in start
                        last_play_id = -1
                        played_cards = []
                        table_combo = [0 for _ in range(4)]
                        exit_order = []
                        landlord_points = 0
                        peasant_points = 0
                        #bottom_cards = [] set in start
                        landlord_phase = True
                        teammate_card = []
                        
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
                        
                        for cards in range(21): # 21 cards
                            for p in range(5): # 5 players
                                hands[p].append(deck.pop())
                        start_packet["bottom_cards"] = deck
                        bottom_cards = deck

                        # find who got flip card
                        flip_id = 0
                        for p in range(5):
                            if flip_card in hands[p]:
                                flip_id = p
                                break
                        start_packet["flip_id"] = flip_id
                        turn_id = flip_id

                        
                        for p, seat in enumerate(seats):
                            if seat["active"] and seat["socket"]:
                                hands[p].sort(key=lambda c: c[0])
                                start_packet["hand"] = hands[p]
                                start_payload = (json.dumps(start_packet) + "\0").encode("utf-8")
                                try:
                                    await seat["socket"].send_bytes(start_payload)
                                except (WebSocketDisconnect, RuntimeError):
                                    seat["active"] = False
                                    seat["socket"] = None
                        start = True

                elif msg_dict["header"] == "PLAY_CARDS":
                    p = msg_dict["sender"]   
                    played_cards = msg_dict["cards"]   
                    table_combo = msg_dict["combo"]
                    turn_id = skip_exited(turn_id)
                    last_play_id = p
                    for card in played_cards:
                        c_int = [int(val) for val in card]
                        
                        if c_int in hands[p]:
                            hands[p].remove(c_int)
                        else:
                            print(f"Error: Card {c_int} not found in hand!")
                            print(hands[p])

                elif msg_dict["header"] == "PASS":
                    turn_id = skip_exited(turn_id)
                    if turn_id == last_play_id:
                        table_combo = [0 for _ in range(4)]
                        played_cards = []

                elif msg_dict["header"] == "EXIT":
                    p = msg_dict["sender"]
                    exit_order.append(p)
                    
                    last_play_id = skip_exited(last_play_id);
    
                    if p in landlord_id:
                        landlord_points += (5-len(exit_order));
                    else:
                        peasant_points += (5-len(exit_order));

                elif msg_dict["header"] == "PFP":
                    p = msg_dict["sender"]
                    pfp[p] = msg_dict["pfp"]
                    print(p + " Base: " + msg_dict["pfp"])
                    print(pfp)

                elif msg_dict["header"] == "LANDLORD":
                    p = msg_dict["sender"]
                    landlord_id.append(p)
                    last_play_id = p
                    turn_id = p
                    hands[p].extend(bottom_cards)
                    hands[p].sort(key=lambda c: c[0])

                elif msg_dict["header"] == "TEAMMATE":
                    found = False
                    teammate_card = msg_dict["teammate"]
                    for p, hand in enumerate(hands):
                        if found:
                            break
                        elif p == msg_dict["sender"]:
                            continue
                        for card in hand[::-1]:
                            if card == teammate_card:
                                found = True
                                for s_id, seat in enumerate(seats):
                                    if seat["active"] and seat["socket"]:
                                        teammate_packet = {"header": "FOUND_TEAMMATE", "sender": p}
                                        teammate_payload = (json.dumps(teammate_packet) + "\0").encode("utf-8")
                                        try:
                                            await seat["socket"].send_bytes(teammate_payload)
                                        except (WebSocketDisconnect, RuntimeError):
                                            seat["active"] = False
                                            seat["socket"] = None
                                landlord_id.append(p)
                                landlord_phase = False
                                break

                elif msg_dict["header"] == "LOBBY":
                    for p in range(5):
                        seats[p]["ready"] = False
                    start = False

                            
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
