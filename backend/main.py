from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import Optional

class Gesture(BaseModel):
    id: int
    name: str
    action: str

class GestureDetectionResult(BaseModel):
    gesture: Optional[str] = None
    confidence: float
    action: Optional[str] = None
    timestamp: float

app = FastAPI(
    title="Hand Gesture Recognition API",
    description="Real-time gesture detection for touchless control",
    version="0.1.0"
)

# CORS — allows our React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data (temporary, will move to proper structure later) ---
SUPPORTED_GESTURES = [
    {"id": 1, "name": "thumbs_up",    "action": "volume_up"},
    {"id": 2, "name": "thumbs_down",  "action": "volume_down"},
    {"id": 3, "name": "open_palm",    "action": "play_pause"},
    {"id": 4, "name": "fist",         "action": "stop"},
    {"id": 5, "name": "peace",        "action": "next_slide"},
]

# --- Routes ---

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Hand Gesture Recognition API",
        "version": "0.1.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/gestures", response_model=list[Gesture])
def get_gestures():
    return SUPPORTED_GESTURES

@app.get("/gestures/{gesture_id}")
def get_gesture(gesture_id: int):
    for gesture in SUPPORTED_GESTURES:
        if gesture["id"] == gesture_id:
            return gesture
    return {"error": "Gesture not found"}