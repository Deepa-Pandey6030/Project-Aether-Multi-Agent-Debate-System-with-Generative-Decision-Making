import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import AuthGuard from './components/layout/AuthGuard'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Theater from './pages/Theater'
import Report from './pages/Report'
import History from './pages/History'
import useAuth from './hooks/useAuth'
import Trace from './pages/Trace'

export default function App() {
  useAuth()
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/debate/:id" element={<AuthGuard><Theater /></AuthGuard>} />
        <Route path="/debate/:id/report" element={<AuthGuard><Report /></AuthGuard>} />
        <Route path="/history" element={<AuthGuard><History /></AuthGuard>} />
        <Route path="/debate/:id/trace" element={<AuthGuard><Trace /></AuthGuard>} />
      </Routes>
    </BrowserRouter>
  )
}