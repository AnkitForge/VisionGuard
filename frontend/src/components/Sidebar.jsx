import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// Icons
const IconHome = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
const IconArchive = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" /></svg>
const IconChart = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: <IconHome /> },
  { to: '/evidence', label: 'Evidence', icon: <IconArchive /> },
  { to: '/analytics', label: 'Analytics', icon: <IconChart /> },
]

function Sidebar() {
  const { user, logout } = useAuth()

  return (
    <aside className="glass h-screen w-full max-w-72 border-r border-white/5 px-6 py-10 flex flex-col">
      <div className="mb-12">
        <p className="text-[10px] uppercase tracking-[0.3em] font-black text-indigo-500/80">Neural System</p>
        <h1 className="mt-1 text-2xl font-black tracking-tight text-white">VisionGuard</h1>
      </div>

      <nav className="space-y-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-4 rounded-2xl px-5 py-3.5 text-sm font-bold transition-all duration-300 ${
                isActive 
                  ? 'bg-indigo-600/20 text-indigo-400 shadow-[0_0_20px_rgba(79,70,229,0.15)] border border-indigo-500/20' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
              }`
            }
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto">
        <div className="mb-6 rounded-3xl bg-black/40 border border-white/5 p-5">
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Operator</p>
          <p className="truncate text-sm font-bold text-slate-200">{user?.email}</p>
        </div>
        <button
          onClick={logout}
          className="btn-danger w-full justify-center py-4 text-xs tracking-widest uppercase"
        >
          System Logout
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
