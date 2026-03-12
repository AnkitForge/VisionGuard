function AlertList({ alerts }) {
  return (
    <section className="glass rounded-2xl p-4">
      <h3 className="mb-3 text-lg font-semibold">Recent Alerts</h3>
      <div className="max-h-[350px] space-y-2 overflow-auto pr-1 scrollbar-thin">
        {alerts.length === 0 ? <p className="text-sm text-slate-400">No alerts yet.</p> : null}
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`rounded-xl border px-3 py-2 ${
              alert.severity === 'high' ? 'border-rose-500/40 bg-rose-500/10' : 'border-amber-500/30 bg-amber-500/10'
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium">{alert.activity_type}</p>
              <span className="text-xs text-slate-300">{(alert.confidence * 100).toFixed(0)}%</span>
            </div>
            <p className="text-xs text-slate-400">{new Date(alert.timestamp).toLocaleString()}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

export default AlertList
