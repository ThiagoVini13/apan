import { useState, useEffect } from 'react'
import './App.css'

interface HealthResponse {
  status: string
}

function App() {
  const [apiStatus, setApiStatus] = useState<string>('Verificando...')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json() as Promise<HealthResponse>)
      .then((data) => setApiStatus(data.status))
      .catch(() => setApiStatus('Offline'))
  }, [])

  return (
    <main>
      <h1>APAN</h1>
      <p>
        Status do Backend: <strong>{apiStatus}</strong>
      </p>
    </main>
  )
}

export default App

