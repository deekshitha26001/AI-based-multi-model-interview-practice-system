import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loginUser } from '../api.js'

/**
 * Login.jsx
 * Simple email-based login page — no password, no OAuth provider.
 * On submit, calls the backend which either finds or creates the user,
 * then stores the returned user object in localStorage for use across the app.
 */
function Login() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!name.trim() || !email.trim()) {
      setError('Please enter both name and email.')
      return
    }

    setLoading(true)
    try {
      const user = await loginUser(name.trim(), email.trim())
      localStorage.setItem('user', JSON.stringify(user))
      navigate('/dashboard')
    } catch (err) {
      setError('Login failed. Please check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-offwhite px-4">
      <div className="app-card w-full max-w-md">
        <h1 className="text-2xl font-bold text-brown-dark mb-1 text-center">
          AI Interview Practice System
        </h1>
        <p className="text-sm text-gray-500 mb-6 text-center">
          Final Year AI & ML Project
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-brown-dark mb-1">
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brown"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-brown-dark mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brown"
            />
          </div>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login
