import { Link, useNavigate } from 'react-router-dom'
import { logout } from '../../api/auth'
import useAuthStore from '../../store/authStore'

export default function Navbar() {
  const { isAuthenticated, logout: clearAuth, user } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    const refresh = localStorage.getItem('refresh_token')
    try { await logout(refresh) } catch {}
    clearAuth()
    navigate('/login')
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-4 border-b border-white/10 bg-black/60 backdrop-blur-md">
      <Link to="/" className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
          <span className="text-white font-black text-sm">A</span>
        </div>
        <span className="text-white font-bold tracking-widest text-sm uppercase">Aether</span>
      </Link>

      <div className="flex items-center gap-6">
        {isAuthenticated ? (
          <>
            <Link to="/history" className="text-white/50 hover:text-white text-sm transition-colors">History</Link>
            <span className="text-white/30 text-sm">{user?.username}</span>
            <button onClick={handleLogout} className="text-white/50 hover:text-white text-sm transition-colors">Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" className="text-white/50 hover:text-white text-sm transition-colors">Login</Link>
            <Link to="/signup" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors">Sign Up</Link>
          </>
        )}
      </div>
    </nav>
  )
}