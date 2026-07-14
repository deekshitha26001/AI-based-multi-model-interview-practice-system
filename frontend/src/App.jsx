import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Interview from './pages/Interview.jsx'
import Report from './pages/Report.jsx'
import History from './pages/History.jsx'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/interview" element={<Interview />} />
      <Route path="/report/:sessionId" element={<Report />} />
      <Route path="/history" element={<History />} />
      {/* Any unknown route redirects back to login */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
