import { createContext, useContext, useMemo, useState } from 'react'
import { api } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('vg_token'))
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('vg_user')
    return raw ? JSON.parse(raw) : null
  })

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    localStorage.setItem('vg_token', data.token)
    localStorage.setItem('vg_user', JSON.stringify(data.user))
    setToken(data.token)
    setUser(data.user)
  }

  const register = async (email, password) => {
    const { data } = await api.post('/auth/register', { email, password })
    localStorage.setItem('vg_token', data.token)
    localStorage.setItem('vg_user', JSON.stringify(data.user))
    setToken(data.token)
    setUser(data.user)
  }

  const logout = () => {
    localStorage.removeItem('vg_token')
    localStorage.removeItem('vg_user')
    setToken(null)
    setUser(null)
  }

  const value = useMemo(() => ({ token, user, isAuthenticated: !!token, login, register, logout }), [token, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return ctx
}
