import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { motion, AnimatePresence } from 'framer-motion'
import { API_BASE_URL, api } from '../services/api'
import LiveFeed from '../components/LiveFeed'
import StatusPanel from '../components/StatusPanel'
import AlertList from '../components/AlertList'
import AlertPopup from '../components/AlertPopup'
import LoadingSpinner from '../components/LoadingSpinner'

const ALLOWED = '.mp4,.avi,.mov,.mkv,.webm'

function beep() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  if (!AudioCtx) return
  const ctx = new AudioCtx()
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.connect(gain)
  gain.connect(ctx.destination)
  osc.frequency.value = 880
  gain.gain.value = 0.1
  osc.start()
  osc.stop(ctx.currentTime + 0.25)
}

function DashboardPage() {
  const [status, setStatus] = useState({ camera_connected: false, model_running: false, processing_fps: 0, total_alerts_today: 0 })
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [popupAlert, setPopupAlert] = useState(null)
  const lastAlertTs = useRef(null)

  // Video upload state
  const [uploadFile, setUploadFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadJobId, setUploadJobId] = useState(null)
  const [uploadJob, setUploadJob] = useState(null)
  const seenAlertIds = useRef(new Set())
  const pollRef = useRef(null)

  const token = localStorage.getItem('vg_token')

  const fetchStatus = async () => {
    try {
      const { data } = await api.get('/system-status')
      setStatus(data)
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to fetch system status')
    }
  }

  const fetchAlerts = async () => {
    try {
      const params = lastAlertTs.current ? { since: lastAlertTs.current } : undefined
      const { data } = await api.get('/alerts', { params })
      const fresh = data.alerts || []
      if (fresh.length > 0) {
        const newest = fresh[0]
        lastAlertTs.current = newest.timestamp
        setAlerts((prev) => [...fresh, ...prev].slice(0, 50))
        setPopupAlert(newest)
        beep()
        setTimeout(() => setPopupAlert(null), 3500)
      }
    } catch {
      // avoid repeated toasts on polling
    }
  }

  const loadInitial = async () => {
    setLoading(true)
    try {
      const [alertsRes, statusRes] = await Promise.all([api.get('/alerts'), api.get('/system-status')])
      const initialAlerts = alertsRes.data.alerts || []
      setAlerts(initialAlerts)
      setStatus(statusRes.data)
      if (initialAlerts[0]) {
        lastAlertTs.current = initialAlerts[0].timestamp
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  const startCamera = async () => {
    try {
      await api.post('/start-camera')
      toast.success('Camera started')
      fetchStatus()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to start camera')
    }
  }

  const stopCamera = async () => {
    try {
      await api.post('/stop-camera')
      toast.success('Camera stopped')
      fetchStatus()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to stop camera')
    }
  }

  // --- Video upload ---
  const onFileChange = (e) => {
    const selected = e.target.files?.[0]
    if (selected) {
      setUploadFile(selected)
      setUploadJobId(null)
      setUploadJob(null)
      seenAlertIds.current.clear()
    }
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    const dropped = e.dataTransfer.files?.[0]
    if (dropped) {
      setUploadFile(dropped)
      setUploadJobId(null)
      setUploadJob(null)
      seenAlertIds.current.clear()
    }
  }, [])

  const uploadVideo = async () => {
    if (!uploadFile) return
    setUploading(true)
    setUploadJob(null)
    seenAlertIds.current.clear()
    try {
      const formData = new FormData()
      formData.append('video', uploadFile)
      const { data } = await api.post('/upload-video', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })
      setUploadJobId(data.job_id)
      toast.success('Video uploaded — analysis started in Live Monitoring')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  // Poll upload job for progress + detections/alerts
  useEffect(() => {
    if (!uploadJobId) return

    const poll = async () => {
      try {
        const { data } = await api.get(`/upload-video/${uploadJobId}/detection`)
        const job = data.job
        setUploadJob(job)

        // Show alerts from upload detections
        if (job?.alerts?.length) {
          for (const alert of job.alerts) {
            if (!seenAlertIds.current.has(alert.id)) {
              seenAlertIds.current.add(alert.id)
              beep()
              setPopupAlert(alert)
              setAlerts((prev) => [alert, ...prev].slice(0, 50))
              setTimeout(() => setPopupAlert(null), 3500)
            }
          }
        }

        if (job?.status === 'completed') {
          toast.success('Video analysis complete!')
          clearInterval(pollRef.current)
        } else if (job?.status === 'error') {
          toast.error(`Analysis error: ${job.error}`)
          clearInterval(pollRef.current)
        }
      } catch { /* ignore polling errors */ }
    }

    poll()
    pollRef.current = setInterval(poll, 2000)
    return () => clearInterval(pollRef.current)
  }, [uploadJobId])

  useEffect(() => {
    loadInitial()
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      fetchStatus()
      fetchAlerts()
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const isUploadProcessing = uploadJob?.status === 'processing'
  const isUploadComplete = uploadJob?.status === 'completed'
  const uploadDetections = uploadJob?.detections || []
  const outputVideoUrl = uploadJob?.output_video
    ? `${API_BASE_URL}/api/upload-video/${uploadJob.id}/output?token=${token}`
    : null

  return (
    <div className="space-y-4">
      <AlertPopup alert={popupAlert} />
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Threat Monitoring Dashboard</h1>
        <div className="flex gap-2">
          <button onClick={startCamera} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950">Start Camera</button>
          <button onClick={stopCamera} className="rounded-lg bg-rose-500 px-4 py-2 text-sm font-semibold text-white">Stop Camera</button>
        </div>
      </motion.div>

      {loading ? <LoadingSpinner label="Loading dashboard..." /> : null}

      {/* Video Upload Section */}
      <section
        className="glass rounded-2xl p-4"
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        <h3 className="mb-3 text-lg font-semibold">Upload Video for Analysis</h3>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex h-20 w-full cursor-pointer items-center justify-center rounded-xl border-2 border-dashed border-white/20 bg-slate-900/50 transition hover:border-cyan-400/50 md:w-auto md:px-8">
            <div className="flex items-center gap-2">
              <svg className="h-6 w-6 text-slate-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
              </svg>
              <span className="text-sm text-slate-300">
                {uploadFile ? uploadFile.name : 'Drop video or click to browse'}
              </span>
              {uploadFile && <span className="text-xs text-slate-500">({(uploadFile.size / 1024 / 1024).toFixed(1)} MB)</span>}
            </div>
            <input type="file" accept={ALLOWED} className="hidden" onChange={onFileChange} />
          </label>
          <button
            onClick={uploadVideo}
            disabled={!uploadFile || uploading || isUploadProcessing}
            className="rounded-lg bg-cyan-500 px-5 py-2.5 text-sm font-semibold text-slate-900 transition hover:bg-cyan-400 disabled:opacity-50"
          >
            {uploading ? 'Uploading...' : isUploadProcessing ? 'Analyzing...' : 'Upload & Analyze'}
          </button>
        </div>

        {/* Progress bar */}
        <AnimatePresence>
          {uploadJob && (isUploadProcessing || isUploadComplete) && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mt-3">
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-slate-400">{isUploadProcessing ? 'Analyzing...' : 'Complete'}</span>
                <span className="font-medium text-cyan-300">{uploadJob.progress}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                <motion.div
                  className={`h-full rounded-full ${isUploadComplete ? 'bg-emerald-500' : 'bg-cyan-500'}`}
                  animate={{ width: `${uploadJob.progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              <div className="mt-1 flex gap-3 text-xs text-slate-500">
                <span>Frames: {uploadJob.processed_frames}/{uploadJob.total_frames}</span>
                <span>Detections: {uploadDetections.length}</span>
                <span>Detector: {uploadJob.detector_type}</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </section>

      {/* Live Feed + Status */}
      <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <LiveFeed
          cameraRunning={status.camera_connected && status.model_running}
          uploadJobId={uploadJobId}
          uploadStatus={uploadJob?.status}
        />
        <StatusPanel status={status} />
      </div>

      {/* Output video after upload completes */}
      {isUploadComplete && outputVideoUrl && (
        <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-2xl p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-lg font-semibold">Analyzed Output</h3>
            <a
              href={`${outputVideoUrl}&download=1`}
              className="rounded-lg bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-slate-900"
            >
              Download
            </a>
          </div>
          <video controls autoPlay className="w-full rounded-xl border border-white/10" src={outputVideoUrl} />
        </motion.section>
      )}

      {/* Live detections from upload */}
      {isUploadProcessing && uploadDetections.length > 0 && (
        <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass rounded-2xl p-4">
          <h3 className="mb-3 text-lg font-semibold text-rose-300">Live Detections</h3>
          <div className="max-h-[250px] space-y-2 overflow-auto pr-1 scrollbar-thin">
            {[...uploadDetections].reverse().slice(0, 20).map((d, idx) => (
              <div key={idx} className={`rounded-xl border px-3 py-2 ${d.severity === 'high' ? 'border-rose-500/40 bg-rose-500/10' : 'border-amber-500/30 bg-amber-500/10'}`}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">{d.activity_type}</p>
                  <span className="text-xs text-slate-300">{(d.confidence * 100).toFixed(0)}%</span>
                </div>
                <p className="text-xs text-slate-400">Frame {d.frame} &middot; {d.time_sec}s</p>
              </div>
            ))}
          </div>
        </motion.section>
      )}

      <AlertList alerts={alerts} />
    </div>
  )
}

export default DashboardPage
