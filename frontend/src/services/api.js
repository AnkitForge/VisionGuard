import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'

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

// Auto-logout on 401 (expired / invalid token)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || ''
      // Don't clear token for login/register calls — those are auth attempts themselves
      if (!url.includes('/auth/login') && !url.includes('/auth/register')) {
        localStorage.removeItem('vg_token')
        localStorage.removeItem('vg_user')
        window.location.replace('/login')
      }
    }
    return Promise.reject(error)
  }
)

export { API_BASE_URL }
