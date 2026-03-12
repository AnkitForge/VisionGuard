import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await register(email, password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      toast.error(err.response?.data?.error || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={onSubmit} className="glass w-full max-w-md rounded-2xl p-8">
        <h1 className="mb-1 text-2xl font-semibold">Create Admin Account</h1>
        <p className="mb-6 text-sm text-slate-400">VisionGuard secure onboarding</p>
        <div className="space-y-4">
          <input className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <input className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password (min 6 chars)" />
          <button disabled={loading} className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-900 transition hover:bg-cyan-400 disabled:opacity-60">
            {loading ? 'Creating...' : 'Register'}
          </button>
          <p className="text-center text-sm text-slate-400">
            Already registered? <Link className="text-cyan-300" to="/login">Login</Link>
          </p>
        </div>
      </form>
    </div>
  )
}

export default RegisterPage
