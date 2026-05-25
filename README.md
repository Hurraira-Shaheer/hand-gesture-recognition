# Hand Gesture Recognition for Touchless Control

A real-time gesture recognition system that controls Spotify playback using hand gestures — no touch required. Built with a Python/FastAPI backend, MediaPipe computer vision pipeline, and a React frontend communicating over WebSockets.

![Demo](docs/demo.gif)

---

## How It Works

A webcam feed is captured in the browser and streamed to the backend at 10 frames per second via WebSocket. Each frame is processed by a MediaPipe hand landmark detection pipeline that identifies 21 keypoints on the hand. Finger states are derived from landmark geometry and classified into gestures, which are mapped to Spotify API actions with a cooldown mechanism to prevent accidental triggers.
Browser (React)
│  WebSocket — base64 encoded frames
▼
FastAPI Backend
│  OpenCV + MediaPipe
▼
Gesture Classifier
│  Spotify Web API
▼
Music Control

---

## Gesture Mappings

| Gesture | Action |
|---------|--------|
| Open Palm | Play / Pause |
| Fist | Stop |
| Thumbs Up | Volume Up (+10%) |
| Thumbs Down | Volume Down (-10%) |
| Peace | Next Track |
| Pointing | Previous Track |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Computer Vision | Python, MediaPipe, OpenCV |
| Backend | FastAPI, WebSockets, Uvicorn |
| Frontend | React, Vite |
| Music API | Spotify Web API (spotipy) |
| Containerization | Docker, Docker Compose |

---

## Project Structure
    hand-gesture-recognition/
    ├── backend/
    │   ├── main.py          # FastAPI app — REST routes + WebSocket endpoint
    │   └── spotify.py       # Spotify Web API integration
    ├── frontend/
    │   └── src/
    │       ├── App.jsx      # Main React component
    │       └── App.css      # Styles
    ├── ml/
    │   ├── gesture_detector.py   # MediaPipe pipeline + gesture classifier
    │   ├── collect_data.py       # Data collection script for ML training
    │   └── train_model.py        # SVM training pipeline (future improvement)
    ├── docs/
    │   └── architecture.md  # Architecture decisions
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    ├── docker-compose.yml
    └── requirements.txt

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Spotify Premium account
- Webcam

### 1. Clone the repository
```bash
git clone https://github.com/Hurraira-Shaheer/hand-gesture-recognition.git
cd hand-gesture-recognition
```

### 2. Set up Spotify credentials

Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), create an app, and add `http://127.0.0.1:8000/callback` as a redirect URI.

Create a `.env` file in the project root:
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/callback

### 3. Authenticate with Spotify

Start the backend once to complete OAuth:
```bash
pip install -r requirements.txt
uvicorn backend.main:app
```

Visit `http://127.0.0.1:8000/spotify/current` — a browser window will open for Spotify login. After authenticating, a `.spotify_cache` file is created. Stop the server.

### 4. Run with Docker
```bash
docker compose up --build
```

Open `http://localhost:5173`, click **Start Detection**, and show your hand to the camera.

---

## Development Setup (without Docker)

```bash
# Backend
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn backend.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Architecture Notes

### Why WebSockets over REST?
Gesture detection runs at 10fps. REST would require 10 HTTP connections per second per client — significant overhead. WebSockets maintain a single persistent connection for bidirectional streaming, reducing latency and connection overhead.

### Why MediaPipe Landmarks over Raw Image Classification?
Processing 21 normalized (x,y) coordinates per frame is orders of magnitude cheaper than running a CNN on raw image data. Landmark extraction also makes the classifier rotation and scale invariant to some degree, and removes background noise entirely.

### Gesture Stabilization
Raw gesture predictions flicker between frames due to minor hand movements. A sliding window stabilizer (6 frames, 60% agreement threshold) smooths predictions before triggering Spotify actions. A 2-second cooldown prevents repeated triggers from held gestures.

### Future Improvements
- **ML Classifier**: An SVM trained on collected landmark data (`ml/train_model.py`) was explored but requires a more robust data collection pipeline with outlier removal and scale normalization for reliable real-world performance. The rule-based classifier was retained for stability.
- **Multi-hand support**: Currently detects one hand only.
- **Custom gesture mapping**: UI for users to remap gestures to actions.

---

## Acknowledgements

- [MediaPipe](https://mediapipe.dev/) for hand landmark detection
- [Spotipy](https://spotipy.readthedocs.io/) for Spotify Web API wrapper
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
