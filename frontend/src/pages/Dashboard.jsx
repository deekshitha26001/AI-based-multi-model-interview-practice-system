import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar.jsx'
import ScoreCard from '../components/ScoreCard.jsx'
import { getDashboard } from '../api.js'

/**
 * Dashboard.jsx
 * Landing page after login. Shows total interviews, average score,
 * recent interview list, and a button to start a new interview.
 */
function Dashboard() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      navigate('/')
      return
    }
    const parsedUser = JSON.parse(storedUser)
    setUser(parsedUser)
    fetchDashboard(parsedUser.id)
  }, [])

  const fetchDashboard = async (userId) => {
    try {
      const data = await getDashboard(userId)
      setDashboardData(data)
    } catch (err) {
      setError('Could not load dashboard data. Please refresh the page.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-offwhite flex items-center justify-center">
        <p className="text-brown-dark">Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-offwhite px-6 py-6 max-w-5xl mx-auto">
      <Navbar />

      <div className="mb-6">
        <h2 className="text-xl font-semibold text-brown-dark">
          Welcome, {user?.name}
        </h2>
        <p className="text-sm text-gray-500">
          Here's a summary of your interview practice so far.
        </p>
      </div>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <ScoreCard
          label="Total Interviews"
          score={dashboardData?.total_interviews ?? 0}
          maxScore={Math.max(dashboardData?.total_interviews ?? 1, 1)}
        />
        <ScoreCard
          label="Average Score"
          score={dashboardData?.average_score ?? 0}
        />
      </div>

      {/* Start New Interview Button */}
      <div className="app-card mb-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h3 className="font-semibold text-brown-dark">Ready for practice?</h3>
          <p className="text-sm text-gray-500">
            Start a new AI-powered mock interview.
          </p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/interview')}>
          Start New Interview
        </button>
      </div>

      {/* Recent Interviews */}
      <div className="app-card">
        <h3 className="font-semibold text-brown-dark mb-4">Recent Interviews</h3>

        {dashboardData?.recent_interviews?.length === 0 ? (
          <p className="text-sm text-gray-500">
            No interviews yet. Start your first one above.
          </p>
        ) : (
          <div className="space-y-3">
            {dashboardData?.recent_interviews?.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between border-b border-gray-100 pb-3 last:border-0"
              >
                <div>
                  <p className="font-medium text-brown-dark">{item.interview_type} Interview</p>
                  <p className="text-xs text-gray-500">{item.created_at}</p>
                </div>
                <p className="text-lg font-bold text-brown">{item.overall_score}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
