import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/evidence', label: 'Evidence' },
  { to: '/analytics', label: 'Analytics' },
]

function Sidebar() {
  const { user, logout } = useAuth()

  return (
    <aside className="glass h-screen w-full max-w-72 border-r border-white/10 px-5 py-6">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-[0.2em] text-cyan-300/80">VisionGuard</p>
        <h1 className="mt-2 text-xl font-semibold">AI Crime Detection</h1>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block rounded-xl px-4 py-3 text-sm transition ${
                isActive ? 'bg-cyan-400/20 text-cyan-200 shadow-glow' : 'text-slate-300 hover:bg-white/10'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto pt-10">
        <div className="mb-3 rounded-xl bg-white/5 px-4 py-3 text-sm">
          <p className="text-slate-400">Logged in</p>
          <p className="truncate text-slate-100">{user?.email}</p>
        </div>
        <button
          onClick={logout}
          className="w-full rounded-xl bg-rose-600/80 px-4 py-2 text-sm font-medium text-white transition hover:bg-rose-600"
        >
          Logout
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
