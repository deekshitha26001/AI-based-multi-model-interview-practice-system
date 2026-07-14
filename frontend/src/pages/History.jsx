import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar.jsx'
import { getHistory } from '../api.js'

/**
 * History.jsx
 * Lists all past completed interviews for the logged-in user.
 * Clicking any entry navigates to its full Report page.
 */
function History() {
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      navigate('/')
      return
    }
    const user = JSON.parse(storedUser)
    fetchHistory(user.id)
  }, [])

  const fetchHistory = async (userId) => {
    try {
      const data = await getHistory(userId)
      setHistory(data)
    } catch (err) {
      setError('Could not load interview history. Please refresh the page.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-offwhite flex items-center justify-center">
        <p className="text-brown-dark">Loading history...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-offwhite px-6 py-6 max-w-4xl mx-auto">
      <Navbar />

      <h2 className="text-xl font-semibold text-brown-dark mb-6">
        Interview History
      </h2>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      {!error && history.length === 0 && (
        <div className="app-card text-center">
          <p className="text-gray-500 mb-4">
            You haven't completed any interviews yet.
          </p>
          <button className="btn-primary" onClick={() => navigate('/interview')}>
            Start Your First Interview
          </button>
        </div>
      )}

      <div className="space-y-3">
        {history.map((item) => (
          <div
            key={item.session_id}
            className="app-card flex items-center justify-between cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => navigate(`/report/${item.session_id}`)}
          >
            <div>
              <p className="font-medium text-brown-dark">
                {item.interview_type} Interview
              </p>
              <p className="text-xs text-gray-500">{item.created_at}</p>
            </div>
            <div className="text-right">
              <p className="text-xl font-bold text-brown">{item.overall_score}</p>
              <p className="text-xs text-gray-500">Overall Score</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default History
