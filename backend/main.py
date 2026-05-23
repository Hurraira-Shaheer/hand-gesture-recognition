from backend.spotify import play_pause, next_track, previous_track, volume_up, volume_down, stop, get_current_track
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import base64
import numpy as np
import cv2
import time
import sys
import os
from fastapi.responses import RedirectResponse
from spotipy.oauth2 import SpotifyOAuth


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.gesture_detector import GestureDetector, GestureStabilizer

GESTURE_ACTION_MAP = {
    "open_palm":   play_pause,
    "fist":        stop,
    "thumbs_up":   volume_up,
    "thumbs_down": volume_down,
    "peace":       next_track,
    "pointing":    previous_track,
}

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

from fastapi.responses import RedirectResponse
from spotipy.oauth2 import SpotifyOAuth
import os

@app.get("/callback")
def spotify_callback(code: str):
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope="user-modify-playback-state user-read-playback-state",
        cache_path=".spotify_cache"
    )
    auth_manager.get_access_token(code)
    return {"status": "authenticated successfully"}

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

@app.get("/gestures")
def get_gestures():
    return {
        "count": len(SUPPORTED_GESTURES),
        "gestures": SUPPORTED_GESTURES
    }

@app.get("/gestures/{gesture_id}")
def get_gesture(gesture_id: int):
    for gesture in SUPPORTED_GESTURES:
        if gesture["id"] == gesture_id:
            return gesture
    return {"error": "Gesture not found"}

# Initialize detector once — not on every connection
# detector = GestureDetector()
detector = GestureDetector()
stabilizer = GestureStabilizer(window_size=10, threshold=0.6)

@app.get("/spotify/current")
def current_track():
    return get_current_track() or {"error": "Nothing playing"}

@app.post("/spotify/{action}")
def spotify_action(action: str):
    actions = {
        "play_pause": play_pause,
        "next": next_track,
        "previous": previous_track,
        "volume_up": volume_up,
        "volume_down": volume_down,
        "stop": stop,
    }
    if action not in actions:
        return {"error": f"Unknown action: {action}"}
    return actions[action]()

last_action_time = 0
last_action_gesture = None
COOLDOWN_SECONDS = 2

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global last_action_time, last_action_gesture
    await websocket.accept()
    print("Client connected")

    try:
        while True:
            data = await websocket.receive_text()

            img_bytes = base64.b64decode(data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                await websocket.send_json({"gesture": "unknown", "confidence": 0.0})
                continue

            landmarks, handedness = detector.get_landmarks(frame)

            if landmarks:
                fingers = detector.get_finger_states(landmarks, handedness)
                raw_gesture = detector.classify_gesture(fingers)
                stable_gesture = stabilizer.update(raw_gesture)

                action_result = None
                current_time = time.time()

                if (stable_gesture in GESTURE_ACTION_MAP and
                    stable_gesture not in ["no_hand", "unknown"] and
                    (stable_gesture != last_action_gesture or
                     current_time - last_action_time > COOLDOWN_SECONDS)):
                    try:
                        action_result = GESTURE_ACTION_MAP[stable_gesture]()
                        last_action_time = current_time
                        last_action_gesture = stable_gesture
                    except Exception as e:
                        action_result = {"error": str(e)}

                await websocket.send_json({
                    "gesture": stable_gesture,
                    "raw_gesture": raw_gesture,
                    "fingers": fingers,
                    "confidence": 1.0,
                    "timestamp": time.time(),
                    "action": action_result
                })
            else:
                stable_gesture = stabilizer.update("no_hand")
                await websocket.send_json({
                    "gesture": stable_gesture,
                    "raw_gesture": "no_hand",
                    "fingers": [],
                    "confidence": 0.0,
                    "timestamp": time.time(),
                    "action": None
                })

    except WebSocketDisconnect:
        print("Client disconnected")