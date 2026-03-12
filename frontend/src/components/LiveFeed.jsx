import { API_BASE_URL } from '../services/api'
import { useAuth } from '../context/AuthContext'

function LiveFeed({ cameraRunning, uploadJobId, uploadStatus }) {
  const { token } = useAuth()
  const cameraFeedUrl = `${API_BASE_URL}/api/video-feed?token=${token}`
  const uploadFeedUrl = uploadJobId
    ? `${API_BASE_URL}/api/upload-video/${uploadJobId}/feed?token=${token}`
    : null

  const isUploadActive = uploadJobId && uploadStatus === 'processing'
  const isStreaming = cameraRunning || isUploadActive

  let label = 'Stopped'
  if (isUploadActive) label = 'Analyzing Upload'
  else if (cameraRunning) label = 'Streaming'

  return (
    <section className="glass rounded-2xl p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Live Monitoring</h2>
        <span className={`rounded-full px-3 py-1 text-xs ${isStreaming ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-500/20 text-slate-300'}`}>
          {label}
        </span>
      </div>
      <div className="overflow-hidden rounded-xl border border-white/10 bg-slate-900">
        {isUploadActive ? (
          <img src={uploadFeedUrl} alt="Upload analysis feed" className="h-[360px] w-full object-cover" />
        ) : cameraRunning ? (
          <img src={cameraFeedUrl} alt="Live feed" className="h-[360px] w-full object-cover" />
        ) : (
          <div className="flex h-[360px] items-center justify-center text-slate-400">No active feed. Start camera or upload a video.</div>
        )}
      </div>
    </section>
  )
}

export default LiveFeed
