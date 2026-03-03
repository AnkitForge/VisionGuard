import { API_BASE_URL } from '../services/api'
import { useAuth } from '../context/AuthContext'

function LiveFeed({ cameraRunning }) {
  const { token } = useAuth()
  const feedUrl = `${API_BASE_URL}/api/video-feed?token=${token}`

  return (
    <section className="glass rounded-2xl p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Live Monitoring</h2>
        <span className={`rounded-full px-3 py-1 text-xs ${cameraRunning ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-500/20 text-slate-300'}`}>
          {cameraRunning ? 'Streaming' : 'Stopped'}
        </span>
      </div>
      <div className="overflow-hidden rounded-xl border border-white/10 bg-slate-900">
        {cameraRunning ? (
          <img src={feedUrl} alt="Live feed" className="h-[360px] w-full object-cover" />
        ) : (
          <div className="flex h-[360px] items-center justify-center text-slate-400">Camera is not running.</div>
        )}
      </div>
    </section>
  )
}

export default LiveFeed
