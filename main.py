from fastapi import FastAPI

app = FastAPI()

@app.get("/test")
async def test_connection():
    return {"status": "connected", "message": "GameMaker has arrived!"}
