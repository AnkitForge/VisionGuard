import { API_BASE_URL } from '../services/api'
import { useAuth } from '../context/AuthContext'

import { useRef } from 'react'

function LiveFeed({ cameraRunning, cameraId = 'default', onStop }) {
  const { token } = useAuth()
  const feedUrl = `${API_BASE_URL}/api/video-feed/${cameraId}?token=${token}`
  const feedRef = useRef(null)

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      feedRef.current?.requestFullscreen().catch(err => console.error(err))
    } else {
      document.exitFullscreen()
    }
  }

  return (
    <section className="glass-card">
      <div className="p-5 flex items-center justify-between border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className={`w-2.5 h-2.5 rounded-full ${cameraRunning ? 'bg-emerald-500 animate-pulse' : 'bg-slate-600'}`} />
          <h2 className="text-sm font-black uppercase tracking-[0.2em] text-slate-200">{cameraId.replace(/_/g, ' ')}</h2>
        </div>
        <div className="flex items-center gap-1">
          {cameraRunning && (
            <>
              <button onClick={toggleFullScreen} className="p-2.5 rounded-2xl hover:bg-white/5 text-slate-500 hover:text-white transition-all" title="Expand View">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
              </button>
              {onStop && (
                <button 
                  onClick={() => { if(window.confirm(`Permanently terminate feed: ${cameraId}?`)) onStop(cameraId) }} 
                  className="p-2.5 rounded-2xl bg-rose-500/10 text-rose-500 hover:bg-rose-500 hover:text-white shadow-lg transition-all active:scale-90"
                  title="Terminate Feed"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              )}
            </>
          )}
        </div>
      </div>
      <div ref={feedRef} className="aspect-video bg-black/40 relative group">
        {cameraRunning ? (
          <img src={feedUrl} alt="Live feed" className="h-full w-full object-contain" />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-600 space-y-2">
             <svg className="w-12 h-12 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
             <p className="text-xs font-bold uppercase tracking-widest opacity-40">Feed Inactive</p>
          </div>
        )}
      </div>
    </section>
  )
}

export default LiveFeed
