import api from './axios'

export const startDebate = (topic, time_budget) =>
  api.post('/debate/start', { topic, time_budget })

export const getDebateStatus = (id) =>
  api.get(`/debate/${id}/status`)

export const getDebate = (id) =>
  api.get(`/debate/${id}`)

export const getReport = (id) =>
  api.get(`/debate/${id}/report`)

export const getTrace = (id) =>
  api.get(`/debate/${id}/trace`)

export const listDebates = (skip = 0, limit = 20) =>
  api.get(`/debates?skip=${skip}&limit=${limit}`)

export const deleteDebate = (id) =>
  api.delete(`/debate/${id}`)