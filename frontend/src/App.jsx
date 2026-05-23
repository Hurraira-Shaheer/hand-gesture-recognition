import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const GESTURE_ACTIONS = {
  open_palm:   'Play / Pause',
  fist:        'Stop',
  thumbs_up:   'Volume Up',
  thumbs_down: 'Volume Down',
  peace:       'Next Track',
  pointing:    'Previous Track',
  no_hand:     '—',
  unknown:     '—',
}

function App() {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const wsRef = useRef(null)
  const intervalRef = useRef(null)

  const [gesture, setGesture] = useState('no_hand')
  const [fingers, setFingers] = useState([])
  const [connected, setConnected] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const [currentTrack, setCurrentTrack] = useState(null)

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      videoRef.current.srcObject = stream
    } catch (err) {
      console.error('Camera error:', err)
    }
  }, [])

  const connectWS = useCallback(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')

    ws.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setGesture(data.gesture)
      setFingers(data.fingers || [])
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)
      setStreaming(false)
    }

    wsRef.current = ws
  }, [])

  const startStreaming = useCallback(() => {
    if (!wsRef.current || !canvasRef.current || !videoRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')

    intervalRef.current = setInterval(() => {
      if (wsRef.current.readyState !== WebSocket.OPEN) return
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height)
      const base64 = canvas.toDataURL('image/jpeg', 0.7).split(',')[1]
      wsRef.current.send(base64)
    }, 100)

    setStreaming(true)
  }, [])

  const stopStreaming = useCallback(() => {
    clearInterval(intervalRef.current)
    setStreaming(false)
  }, [])

  // Poll current track every 3 seconds
  useEffect(() => {
    const fetchTrack = () => {
      fetch('http://127.0.0.1:8000/spotify/current')
        .then(res => res.json())
        .then(data => {
          if (!data.error) setCurrentTrack(data)
        })
        .catch(() => {})
    }
    fetchTrack()
    const interval = setInterval(fetchTrack, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    startCamera()
    connectWS()

    return () => {
      clearInterval(intervalRef.current)
      wsRef.current?.close()
    }
  }, [])

  const fingerNames = ['Thumb', 'Index', 'Middle','Ring', 'Pinky']

  return (
    <div className="app">
      <header>
        <h1>Hand Gesture Recognition</h1>
        <div className={`status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '● Connected' : '○ Disconnected'}
        </div>
      </header>

      <main>
        <div className="camera-section">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            width={640}
            height={480}
          />
          <canvas
            ref={canvasRef}
            width={320}
            height={240}
            style={{ display: 'none' }}
          />
          <div className="camera-controls">
            {!streaming
              ? <button onClick={startStreaming} disabled={!connected}>Start Detection</button>
              : <button onClick={stopStreaming} className="stop">Stop Detection</button>
            }
          </div>
        </div>

        <div className="info-section">

          {currentTrack && (
            <div className="now-playing">
              <div className="section-label">Now Playing</div>
              <div className="track-info">
                {currentTrack.cover_url && (
                  <img src={currentTrack.cover_url} alt="album cover" className="album-cover" />
                )}
                <div className="track-details">
                  <div className="track-name">{currentTrack.name}</div>
                  <div className="track-artist">{currentTrack.artist}</div>
                  <div className="track-volume">Volume: {currentTrack.volume}%</div>
                </div>
              </div>
            </div>
          )}

          <div className="gesture-display">
            <div className="gesture-label">Detected Gesture</div>
            <div className="gesture-name">{gesture.replace('_', ' ')}</div>
            <div className="gesture-action">{GESTURE_ACTIONS[gesture] || '—'}</div>
          </div>

          <div className="finger-states">
            <div className="section-label">Finger States</div>
            <div className="fingers">
              {fingerNames.map((name, i) => (
                <div key={name} className={`finger ${fingers[i] ? 'extended' : 'closed'}`}>
                  <span className="finger-name">{name}</span>
                  <span className="finger-dot">{fingers[i] ? '●' : '○'}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="gesture-grid">
            <div className="section-label">All Gestures</div>
            {Object.entries(GESTURE_ACTIONS)
              .filter(([g]) => !['no_hand', 'unknown'].includes(g))
              .map(([g, action]) => (
                <div key={g} className={`gesture-row ${gesture === g ? 'active' : ''}`}>
                  <span>{g.replace('_', ' ')}</span>
                  <span>{action}</span>
                </div>
              ))}
          </div>

        </div>
      </main>
    </div>
  )
}

export default App