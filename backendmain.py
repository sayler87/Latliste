import os
import json
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket, WebSocketDisconnect
from pathlib import Path

# --- Stier ---
DATA_DIR = Path("app.html")
DATA_FILE = DATA_DIR / "departures.json"

# --- Opprett data-mappe og fil hvis ikke eksisterer ---
DATA_DIR.mkdir(exist_ok=True)
if not DATA_FILE.exists():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# --- FastAPI app ---
app = FastAPI(title="Transportsystem API", version="1.0")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tillat alle (endre i produksjon)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except RuntimeError:
                # Håndter lukkede forbindelser
                self.disconnect(connection)

manager = ConnectionManager()

# --- Hjelpefunksjoner ---
def load_departures():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_departures(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- API-ruter ---
@app.get("/api/departures")
async def get_departures():
    return load_departures()

@app.post("/api/departures")
async def add_or_update_departure(departure: dict):
    departures = load_departures()
    existing = next((d for d in departures if d["id"] == departure["id"]), None)

    if existing:
        departures = [d if d["id"] != departure["id"] else departure for d in departures]
    else:
        departures.append(departure)

    save_departures(departures)
    await manager.broadcast({"type": "update", "data": departures})
    return {"status": "saved"}

@app.delete("/api/departures/{departure_id}")
async def delete_departure(departure_id: int):
    departures = load_departures()
    new_departures = [d for d in departures if d["id"] != departure_id]

    if len(departures) == len(new_departures):
        raise HTTPException(status_code=404, detail="Avgang ikke funnet")

    save_departures(new_departures)
    await manager.broadcast({"type": "update", "data": new_departures})
    return {"status": "deleted"}

@app.post("/api/clear")
async def clear_all():
    save_departures([])
    await manager.broadcast({"type": "update", "data": []})
    return {"status": "cleared"}

@app.post("/api/upload")
async def upload_backup(file: UploadFile = File(...)):
    try:
        content = await file.read()
        data = json.loads(content)
        if isinstance(data, list):
            save_departures(data)
            await manager.broadcast({"type": "update", "data": data})
            return {"status": "uploaded", "count": len(data)}
        else:
            raise ValueError("JSON må være en liste")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ugyldig JSON: {str(e)}")

# --- WebSocket ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Vi bruker WebSocket for ut-sending, ikke mottak
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Statisk frontend (valgfritt) ---
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")