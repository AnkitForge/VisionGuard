function LoadingSpinner({ label = 'Loading...' }) {
  return (
    <div className="flex items-center gap-3 text-slate-300">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-cyan-300/30 border-t-cyan-300" />
      <span className="text-sm">{label}</span>
    </div>
  )
}

export default LoadingSpinner
