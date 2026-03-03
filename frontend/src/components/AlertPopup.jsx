import { AnimatePresence, motion } from 'framer-motion'

function AlertPopup({ alert }) {
  return (
    <AnimatePresence>
      {alert ? (
        <motion.div
          key={alert.id}
          initial={{ opacity: 0, y: -24 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -24 }}
          className={`fixed right-4 top-4 z-50 w-[320px] rounded-2xl border p-4 shadow-2xl ${
            alert.severity === 'high' ? 'border-rose-400/40 bg-rose-900/70' : 'border-amber-300/30 bg-amber-900/60'
          }`}
        >
          <p className="text-sm font-semibold">{alert.activity_type} detected</p>
          <p className="mt-1 text-xs text-slate-100/80">Confidence: {(alert.confidence * 100).toFixed(0)}%</p>
          <p className="text-xs text-slate-100/70">{new Date(alert.timestamp).toLocaleString()}</p>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}

export default AlertPopup
