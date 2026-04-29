function StatusBadge({ ok, label, icon }) {
  return (
    <div className="flex items-center justify-between rounded-2xl bg-white/5 px-4 py-3 border border-white/5">
      <div className="flex items-center gap-3">
        <span className="text-slate-400">{icon}</span>
        <span className="text-sm font-semibold text-slate-200">{label}</span>
      </div>
      <span className={`rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-widest ${ok ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
        {ok ? 'Active' : 'Offline'}
      </span>
    </div>
  )
}

function StatusPanel({ status }) {
  return (
    <section className="glass-card p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold tracking-tight">System Core</h3>
        <div className="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-[10px] font-bold tracking-widest uppercase">Secured</div>
      </div>
      <div className="space-y-3">
        <StatusBadge ok={status.camera_connected} label="Surveillance" icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>} />
        <StatusBadge ok={status.model_running} label="AI Engine" icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>} />
        
        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="rounded-2xl bg-black/20 p-4 border border-white/5">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Inference</p>
            <p className="text-xl font-black text-indigo-400">{status.processing_fps ?? 0}<span className="text-xs ml-1 text-slate-600">FPS</span></p>
          </div>
          <div className="rounded-2xl bg-black/20 p-4 border border-white/5">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Incidents</p>
            <p className="text-xl font-black text-rose-400">{status.total_alerts_today ?? 0}</p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default StatusPanel
