import { useState } from 'react'
import { Home } from './pages/Home'
import { Overview } from './pages/Overview'

function App() {
  const [entered, setEntered] = useState(false)
  return entered ? <Overview onBack={() => setEntered(false)} /> : <Home onEnter={() => setEntered(true)} />
}

export default App
