import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
const AUTH_TOKEN_KEY = 'vg_token'
const AUTH_USER_KEY = 'vg_user'

export function clearStoredAuth() {
  localStorage.removeItem(AUTH_TOKEN_KEY)
  localStorage.removeItem(AUTH_USER_KEY)
}

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(AUTH_TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearStoredAuth()

      const currentPath = window.location.pathname
      const isAuthPage = currentPath === '/login' || currentPath === '/register'

      if (!isAuthPage) {
        window.location.replace('/login')
      }
    }

    return Promise.reject(error)
  }
)

export { API_BASE_URL }
