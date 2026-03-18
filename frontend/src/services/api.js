import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('vg_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export { API_BASE_URL }
