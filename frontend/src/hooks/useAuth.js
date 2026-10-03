import { useEffect } from 'react'
import { getMe } from '../api/auth'
import useAuthStore from '../store/authStore'

export default function useAuth() {
  const { setUser, isAuthenticated } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated) {
      getMe()
        .then(({ data }) => setUser(data))
        .catch(() => {})
    }
  }, [])
}