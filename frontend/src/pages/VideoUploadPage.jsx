import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { motion, AnimatePresence } from 'framer-motion'
import { API_BASE_URL, api } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import AlertPopup from '../components/AlertPopup'

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

function VideoUploadPage() {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [job, setJob] = useState(null)
  const [popupAlert, setPopupAlert] = useState(null)
  const seenAlertIds = useRef(new Set())
  const eventSourceRef = useRef(null)

  const token = useMemo(() => localStorage.getItem('vg_token'), [])

  const onFileChange = (e) => {
    const selected = e.target.files?.[0]
    if (selected) {
      setFile(selected)
      setJobId(null)
      setJob(null)
      seenAlertIds.current.clear()
    }
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    const dropped = e.dataTransfer.files?.[0]
    if (dropped) {
      setFile(dropped)
      setJobId(null)
      setJob(null)
      seenAlertIds.current.clear()
    }
  }, [])

  const uploadVideo = async () => {
    if (!file) return
    setUploading(true)
    setJob(null)
    seenAlertIds.current.clear()
    try {
      const formData = new FormData()
      formData.append('video', file)
      const { data } = await api.post('/upload-video', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })
      setJobId(data.job_id)
      toast.success('Video uploaded — processing started')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  // Poll job status via SSE stream
  useEffect(() => {
    if (!jobId || !token) return

    const url = `${API_BASE_URL}/api/upload-video/${jobId}/stream?token=${token}`
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setJob(data)

        // Show popup for new alerts
        if (data.alerts?.length) {
          for (const alert of data.alerts) {
            if (!seenAlertIds.current.has(alert.id)) {
              seenAlertIds.current.add(alert.id)
              beep()
              setPopupAlert(alert)
              setTimeout(() => setPopupAlert(null), 3500)
            }
          }
        }

        if (data.status === 'completed' || data.status === 'error') {
          es.close()
          if (data.status === 'completed') {
            toast.success('Video processing complete!')
          } else if (data.error) {
            toast.error(`Processing error: ${data.error}`)
          }
        }
      } catch { /* ignore parse errors */ }
    }

    es.onerror = () => {
      es.close()
    }

    return () => {
      es.close()
    }
  }, [jobId, token])

  const outputVideoUrl = job?.output_video
    ? `${API_BASE_URL}/api/upload-video/${job.id}/output?token=${token}`
    : null

  const isProcessing = job?.status === 'processing'
  const isCompleted = job?.status === 'completed'
  const isError = job?.status === 'error'
  const detections = job?.detections || []
  const alerts = job?.alerts || []

  return (
    <div className="space-y-4">
      <AlertPopup alert={popupAlert} />
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-semibold">Video Upload & Analysis</h1>
        <p className="mt-1 text-sm text-slate-400">Upload a video to run theft detection and view results live</p>
      </motion.div>

      {/* Upload Section */}
      <section
        className="glass rounded-2xl p-6"
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        <div className="flex flex-col items-center gap-4 md:flex-row">
          <label className="flex h-40 w-full cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-white/20 bg-slate-900/50 transition hover:border-cyan-400/50 md:w-1/2">
            <svg className="mb-2 h-10 w-10 text-slate-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
            </svg>
            <span className="text-sm text-slate-300">
              {file ? file.name : 'Drop video here or click to browse'}
            </span>
            {file && <span className="mt-1 text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(1)} MB</span>}
            <input type="file" accept={ALLOWED} className="hidden" onChange={onFileChange} />
          </label>

          <div className="flex flex-col items-start gap-2">
            <button
              onClick={uploadVideo}
              disabled={!file || uploading || isProcessing}
              className="rounded-lg bg-cyan-500 px-6 py-3 text-sm font-semibold text-slate-900 transition hover:bg-cyan-400 disabled:opacity-50"
            >
              {uploading ? 'Uploading...' : isProcessing ? 'Processing...' : 'Upload & Analyze'}
            </button>
            <p className="text-xs text-slate-500">Supported: MP4, AVI, MOV, MKV, WebM (max 200 MB)</p>
          </div>
        </div>
      </section>

      {/* Progress Bar */}
      <AnimatePresence>
        {job && (isProcessing || isCompleted) && (
          <motion.section
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-2xl p-4"
          >
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="text-slate-300">
                {isProcessing ? 'Analyzing video...' : 'Analysis complete'}
              </span>
              <span className="font-medium text-cyan-300">{job.progress}%</span>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-slate-800">
              <motion.div
                className={`h-full rounded-full ${isCompleted ? 'bg-emerald-500' : 'bg-cyan-500'}`}
                initial={{ width: 0 }}
                animate={{ width: `${job.progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
            <div className="mt-2 flex gap-4 text-xs text-slate-400">
              <span>Frames: {job.processed_frames} / {job.total_frames}</span>
              <span>Detections: {detections.length}</span>
              <span>Alerts: {alerts.length}</span>
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      {isError && (
        <div className="glass rounded-2xl border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
          Processing failed: {job.error}
        </div>
      )}

      {/* Output Video + Detections Grid */}
      {isCompleted && (
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid gap-4 xl:grid-cols-[2fr_1fr]"
        >
          {/* Output Video */}
          <section className="glass rounded-2xl p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Output Video</h2>
              {outputVideoUrl && (
                <a
                  href={`${outputVideoUrl}&download=1`}
                  className="rounded-lg bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-slate-900"
                >
                  Download
                </a>
              )}
            </div>
            {outputVideoUrl ? (
              <video
                controls
                autoPlay
                className="w-full rounded-xl border border-white/10"
                src={outputVideoUrl}
              />
            ) : (
              <div className="flex h-[360px] items-center justify-center text-slate-400">
                No output available.
              </div>
            )}
          </section>

          {/* Detections Panel */}
          <section className="glass rounded-2xl p-4">
            <h3 className="mb-3 text-lg font-semibold">Detections & Alerts</h3>

            {/* Summary */}
            <div className="mb-3 grid grid-cols-2 gap-2">
              <div className="rounded-xl bg-white/5 px-3 py-2 text-center">
                <p className="text-2xl font-semibold text-cyan-300">{detections.length}</p>
                <p className="text-xs text-slate-400">Detections</p>
              </div>
              <div className="rounded-xl bg-white/5 px-3 py-2 text-center">
                <p className="text-2xl font-semibold text-rose-300">{alerts.length}</p>
                <p className="text-xs text-slate-400">Alerts Sent</p>
              </div>
            </div>

            {/* Detection list */}
            <div className="max-h-[400px] space-y-2 overflow-auto pr-1 scrollbar-thin">
              {detections.length === 0 && (
                <p className="text-sm text-slate-400">No theft activity detected.</p>
              )}
              {detections.map((d, idx) => (
                <div
                  key={idx}
                  className={`rounded-xl border px-3 py-2 ${
                    d.severity === 'high'
                      ? 'border-rose-500/40 bg-rose-500/10'
                      : 'border-amber-500/30 bg-amber-500/10'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">{d.activity_type}</p>
                    <span className="text-xs text-slate-300">
                      {(d.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Frame {d.frame} &middot; {d.time_sec}s
                  </p>
                </div>
              ))}
            </div>

            {/* Alert list */}
            {alerts.length > 0 && (
              <>
                <h4 className="mb-2 mt-4 text-sm font-semibold text-rose-300">Generated Alerts</h4>
                <div className="max-h-[200px] space-y-2 overflow-auto pr-1 scrollbar-thin">
                  {alerts.map((a) => (
                    <div
                      key={a.id}
                      className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-3 py-2"
                    >
                      <p className="text-sm font-medium">{a.activity_type}</p>
                      <p className="text-xs text-slate-400">
                        {new Date(a.timestamp).toLocaleString()} &middot;{' '}
                        {(a.confidence * 100).toFixed(0)}% &middot; {a.severity}
                      </p>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>
        </motion.div>
      )}

      {/* Live Detections while processing */}
      {isProcessing && detections.length > 0 && (
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass rounded-2xl p-4"
        >
          <h3 className="mb-3 text-lg font-semibold">Live Detections</h3>
          <div className="max-h-[300px] space-y-2 overflow-auto pr-1 scrollbar-thin">
            {[...detections].reverse().map((d, idx) => (
              <div
                key={idx}
                className={`rounded-xl border px-3 py-2 ${
                  d.severity === 'high'
                    ? 'border-rose-500/40 bg-rose-500/10'
                    : 'border-amber-500/30 bg-amber-500/10'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">{d.activity_type}</p>
                  <span className="text-xs text-slate-300">
                    {(d.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  Frame {d.frame} &middot; {d.time_sec}s
                </p>
              </div>
            ))}
          </div>
        </motion.section>
      )}
    </div>
  )
}

export default VideoUploadPage
