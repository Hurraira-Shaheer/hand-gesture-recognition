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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.gesture_detector import GestureDetector, GestureStabilizer

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        while True:
            # Receive base64 encoded frame from browser
            data = await websocket.receive_text()

            # Decode base64 → bytes → numpy array → OpenCV image
            img_bytes = base64.b64decode(data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                await websocket.send_json({"gesture": "unknown", "confidence": 0.0})
                continue

            # # Run detection
            # landmarks = detector.get_landmarks(frame)

            # if landmarks:
            #     fingers = detector.get_finger_states(landmarks)
            #     gesture = detector.classify_gesture(fingers)
            #     await websocket.send_json({
            #         "gesture": gesture,
            #         "fingers": fingers,
            #         "confidence": 1.0,
            #         "timestamp": time.time()
            #     })
            # else:
            #     await websocket.send_json({
            #         "gesture": "no_hand",
            #         "fingers": [],
            #         "confidence": 0.0,
            #         "timestamp": time.time()
            #     })
            
            # Run detection
            landmarks, handedness = detector.get_landmarks(frame)

            if landmarks:
                fingers = detector.get_finger_states(landmarks, handedness)
                raw_gesture = detector.classify_gesture(fingers)
                stable_gesture = stabilizer.update(raw_gesture)  # smooth it

                await websocket.send_json({
                    "gesture": stable_gesture,
                    "raw_gesture": raw_gesture,      # useful for debugging
                    "fingers": fingers,
                    "confidence": 1.0,
                    "timestamp": time.time()
                })
            else:
                stable_gesture = stabilizer.update("no_hand")
                await websocket.send_json({
                    "gesture": stable_gesture,
                    "raw_gesture": "no_hand",
                    "fingers": [],
                    "confidence": 0.0,
                    "timestamp": time.time()
                })            
            # if landmarks:
            #     fingers = detector.get_finger_states(landmarks, handedness)
            #     gesture = detector.classify_gesture(fingers)
            #     await websocket.send_json({
            #         "gesture": gesture,
            #         "fingers": fingers,
            #         "confidence": 1.0,
            #         "timestamp": time.time()
            #     })
            # else:
            #     await websocket.send_json({
            #         "gesture": "no_hand",
            #         "fingers": [],
            #         "confidence": 0.0,
            #         "timestamp": time.time()
            #     })

    except WebSocketDisconnect:
        print("Client disconnected")