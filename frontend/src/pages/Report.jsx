import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar.jsx'
import ScoreCard from '../components/ScoreCard.jsx'
import { getReport } from '../api.js'

/**
 * Report.jsx
 * Shows the final report for a completed interview session:
 * overall/communication/technical/confidence scores, strengths,
 * weaknesses, and suggestions.
 */
function Report() {
  const { sessionId } = useParams()
  const navigate = useNavigate()

  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      navigate('/')
      return
    }
    fetchReport()
  }, [sessionId])

  const fetchReport = async () => {
    try {
      const data = await getReport(sessionId)
      setReport(data)
    } catch (err) {
      setError('Could not load this report. It may not exist or the session was not completed.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-offwhite flex items-center justify-center">
        <p className="text-brown-dark">Loading report...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-offwhite px-6 py-6 max-w-3xl mx-auto">
        <Navbar />
        <div className="app-card">
          <p className="text-red-600">{error}</p>
          <button className="btn-primary mt-4" onClick={() => navigate('/dashboard')}>
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-offwhite px-6 py-6 max-w-4xl mx-auto">
      <Navbar />

      <h2 className="text-xl font-semibold text-brown-dark mb-6">
        Interview Report
      </h2>

      {/* Score Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <ScoreCard label="Overall Score" score={report.overall_score} />
        <ScoreCard label="Communication" score={report.communication_score} />
        <ScoreCard label="Technical" score={report.technical_score} />
        <ScoreCard label="Confidence" score={report.confidence_score} />
      </div>

      {/* Strengths */}
      <div className="app-card mb-4">
        <h3 className="font-semibold text-brown-dark mb-3">Strengths</h3>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
          {report.strengths.map((point, idx) => (
            <li key={idx}>{point}</li>
          ))}
        </ul>
      </div>

      {/* Weaknesses */}
      <div className="app-card mb-4">
        <h3 className="font-semibold text-brown-dark mb-3">Weaknesses</h3>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
          {report.weaknesses.map((point, idx) => (
            <li key={idx}>{point}</li>
          ))}
        </ul>
      </div>

      {/* Suggestions */}
      <div className="app-card mb-8">
        <h3 className="font-semibold text-brown-dark mb-3">Suggestions</h3>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
          {report.suggestions.map((point, idx) => (
            <li key={idx}>{point}</li>
          ))}
        </ul>
      </div>

      <div className="flex gap-3">
        <button className="btn-primary" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
        <button
          className="btn-primary bg-brown-light hover:bg-brown"
          onClick={() => navigate('/interview')}
        >
          Start Another Interview
        </button>
      </div>
    </div>
  )
}

export default Report
