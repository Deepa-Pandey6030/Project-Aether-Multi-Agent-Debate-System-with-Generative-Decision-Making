import api from './axios'

export const signup = (email, username, password) =>
  api.post('/auth/signup', { email, username, password })

export const login = (username, password) =>
  api.post('/auth/login', { username, password })

export const refresh = (refresh_token) =>
  api.post('/auth/refresh', { refresh_token })

export const logout = (refresh_token) =>
  api.post('/auth/logout', { refresh_token })

export const getMe = () => api.get('/auth/me')