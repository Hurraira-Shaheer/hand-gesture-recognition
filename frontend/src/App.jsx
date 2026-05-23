import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [gestures, setGestures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/gestures')
      .then(res => res.json())
      .then(data => {
        setGestures(data.gestures)
        setLoading(false)
      })
      .catch(err => {
        setError('Could not reach API')
        setLoading(false)
      })
  }, [])

  return (
    <div className="app">
      <h1>Hand Gesture Recognition</h1>
      <p className="subtitle">Touchless Control System</p>

      <section className="gestures">
        <h2>Supported Gestures</h2>

        {loading && <p>Loading...</p>}
        {error && <p className="error">{error}</p>}

        <div className="gesture-grid">
          {gestures.map(gesture => (
            <div key={gesture.id} className="gesture-card">
              <span className="gesture-name">{gesture.name}</span>
              <span className="gesture-action">→ {gesture.action}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default App