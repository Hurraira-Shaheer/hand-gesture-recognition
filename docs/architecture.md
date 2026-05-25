# Architecture

## System Overview

The system consists of two services — a Python backend and a React frontend — communicating over WebSockets for real-time gesture streaming.

## Data Flow

1. Browser captures webcam frames using `getUserMedia` API
2. Frames are drawn onto a hidden canvas at 10fps
3. Canvas frames are exported as base64 JPEG and sent over WebSocket
4. FastAPI backend decodes frames using OpenCV
5. MediaPipe processes each frame and returns 21 hand landmarks
6. Gesture classifier derives finger states from landmark geometry
7. GestureStabilizer smooths predictions across a 6-frame window
8. If gesture changed and cooldown elapsed, Spotify API action fires
9. Result sent back to frontend over WebSocket
10. React updates UI with current gesture and finger states

## Key Design Decisions

### Separation of ML and Backend
`ml/gesture_detector.py` is intentionally separate from the backend. The detector can be tested standalone (`ml/test_detector.py`) without running the full server. This separation makes it easy to swap the classifier without touching API code.

### Stateless WebSocket Handler
The WebSocket endpoint in `main.py` holds no per-connection state except `last_action_time` and `last_action_gesture` as module-level globals. For a single-user local application this is acceptable. A multi-user deployment would require per-connection state management.

### Spotify Token Caching
The `.spotify_cache` file persists the OAuth token between restarts. In Docker, this file is mounted as a volume so the container doesn't lose authentication on restart.

## Limitations

- **Single hand only**: MediaPipe is configured for `max_num_hands=1`
- **Lighting dependent**: Rule-based landmark geometry is sensitive to poor detection confidence in low light
- **Local only**: No deployment configuration — designed for local use