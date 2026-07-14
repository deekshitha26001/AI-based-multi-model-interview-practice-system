import { useNavigate, useLocation } from 'react-router-dom'

/**
 * Navbar.jsx
 * Simple top navigation bar shown on Dashboard, Interview, Report, and History pages.
 * Not shown on the Login page.
 */
function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    localStorage.removeItem('user')
    navigate('/')
  }

  const linkClass = (path) =>
    `px-4 py-2 rounded-lg font-medium transition-colors ${
      location.pathname === path
        ? 'bg-brown text-white'
        : 'text-brown-dark hover:bg-brown-light hover:text-white'
    }`

  return (
    <nav className="flex items-center justify-between bg-white px-6 py-4 shadow-sm rounded-card mb-6">
      <h1 className="text-lg font-semibold text-brown-dark">
        AI Interview Practice System
      </h1>

      <div className="flex items-center gap-2">
        <button className={linkClass('/dashboard')} onClick={() => navigate('/dashboard')}>
          Dashboard
        </button>
        <button className={linkClass('/history')} onClick={() => navigate('/history')}>
          History
        </button>
        <button
          className="px-4 py-2 rounded-lg font-medium text-brown-dark hover:bg-red-100 transition-colors"
          onClick={handleLogout}
        >
          Logout
        </button>
      </div>
    </nav>
  )
}

export default Navbar
