const WebSocket = require("ws");

const PORT = process.env.PORT || 3000;
const wss = new WebSocket.Server({ port: PORT });

let players = [];

wss.on("connection", (ws) => {
    if (players.length >= 5) {
        ws.close();
        return;
    }

    players.push(ws);
    console.log("Player joined:", players.length);

    ws.on("message", (msg) => {
        // broadcast to everyone
        for (let p of players) {
            if (p.readyState === WebSocket.OPEN) {
                p.send(msg.toString());
            }
        }
    });

    ws.on("close", () => {
        players = players.filter(p => p !== ws);
        console.log("Player left:", players.length);
    });
});

console.log("Server running on", PORT);
