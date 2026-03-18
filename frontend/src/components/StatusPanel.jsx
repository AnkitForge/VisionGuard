function StatusBadge({ ok, label }) {
  return (
    <div className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-2">
      <span className="text-sm text-slate-300">{label}</span>
      <span className={`rounded-full px-2 py-0.5 text-xs ${ok ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
        {ok ? 'Online' : 'Offline'}
      </span>
    </div>
  )
}

function StatusPanel({ status }) {
  return (
    <section className="glass rounded-2xl p-4">
      <h3 className="mb-3 text-lg font-semibold">System Status</h3>
      <div className="space-y-2">
        <StatusBadge ok={status.camera_connected} label="Camera" />
        <StatusBadge ok={status.model_running} label="Model" />
        <div className="rounded-xl bg-white/5 px-3 py-2 text-sm text-slate-200">FPS: {status.processing_fps ?? 0}</div>
        <div className="rounded-xl bg-white/5 px-3 py-2 text-sm text-slate-200">Alerts Today: {status.total_alerts_today ?? 0}</div>
      </div>
    </section>
  )
}

export default StatusPanel
