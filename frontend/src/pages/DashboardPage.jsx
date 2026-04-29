import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../services/api'
import LiveFeed from '../components/LiveFeed'
import StatusPanel from '../components/StatusPanel'
import AlertList from '../components/AlertList'
import AlertPopup from '../components/AlertPopup'
import LoadingSpinner from '../components/LoadingSpinner'

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

// Icons
const IconPlus = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-0h6m-6 0H6" /></svg>
const IconUpload = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
const IconVideo = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>

function DashboardPage() {
  const [status, setStatus] = useState({ cameras: [], total_alerts_today: 0 })
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [popupAlert, setPopupAlert] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [showAddCam, setShowAddCam] = useState(false)
  const [newCam, setNewCam] = useState({ id: '', source: '' })

  const fileInputRef = useRef(null)
  const lastAlertTs = useRef(null)

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
      setAlerts(alertsRes.data.alerts || [])
      setStatus(statusRes.data)
      if (alertsRes.data.alerts?.[0]) {
        lastAlertTs.current = alertsRes.data.alerts[0].timestamp
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  const startCamera = async (id = 'default', source = '0') => {
    if (!id || !source) return toast.error('Please provide name and source')
    try {
      await api.post('/start-camera', { id, source })
      toast.success(`Camera ${id} connected`)
      fetchStatus()
      setShowAddCam(false)
      setNewCam({ id: '', source: '' })
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to start camera')
    }
  }

  const stopCamera = async (id) => {
    try {
      await api.post('/stop-camera', { id })
      toast.success(`Feed ${id} disconnected`)
      fetchStatus()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to stop camera')
    }
  }

  const uploadVideo = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    setUploading(true)
    const toastId = toast.loading('Processing demo clip...')
    try {
      await api.post('/upload-video', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      toast.success('Demo feed active!', { id: toastId })
      fetchStatus()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed', { id: toastId })
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const deleteAlert = async (id) => {
    try {
      await api.delete(`/alerts/${id}`)
      setAlerts((prev) => prev.filter((a) => a.id !== id))
      toast.success('Alert cleared')
    } catch {
      toast.error('Failed to clear alert')
    }
  }

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

  return (
    <div className="max-w-[1600px] mx-auto space-y-8 pb-10">
      <AlertPopup alert={popupAlert} />
      
      {/* Premium Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-wrap items-end justify-between gap-6 border-b border-white/5 pb-8">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-indigo-500 animate-pulse glow-indigo" />
            <h1 className="text-4xl font-extrabold tracking-tight text-gradient">VisionGuard <span className="text-indigo-400">Live</span></h1>
          </div>
          <p className="text-slate-400 font-medium">Neural Threat Detection & Multi-Feed Surveillance</p>
        </div>
        <div className="flex gap-4">
          <input type="file" accept="video/*" className="hidden" ref={fileInputRef} onChange={uploadVideo} />
          <button onClick={() => fileInputRef.current?.click()} disabled={uploading} className="btn-secondary group">
            <span className="opacity-70 group-hover:opacity-100 transition-opacity"><IconUpload /></span>
            Upload Demo
          </button>
          <button onClick={() => setShowAddCam(!showAddCam)} className="btn-primary">
            <IconPlus />
            Add CCTV Feed
          </button>
        </div>
      </motion.div>

      {/* Add Camera Form */}
      <AnimatePresence>
        {showAddCam && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <div className="glass-card p-8 border-indigo-500/20 glow-indigo mb-8">
              <div className="flex items-center gap-4 mb-6">
                <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-400"><IconVideo /></div>
                <div>
                  <h3 className="text-xl font-bold">New Surveillance Feed</h3>
                  <p className="text-sm text-slate-400">Configure RTSP or local camera source</p>
                </div>
              </div>
              <div className="grid gap-6 sm:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500 ml-1">Feed Identifier</label>
                  <input type="text" placeholder="e.g. Warehouse_East" value={newCam.id} onChange={e => setNewCam({...newCam, id: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-2xl px-5 py-3 outline-none focus:border-indigo-500/50 transition-colors" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500 ml-1">Source URL / Index</label>
                  <input type="text" placeholder="rtsp://... or 0" value={newCam.source} onChange={e => setNewCam({...newCam, source: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-2xl px-5 py-3 outline-none focus:border-indigo-500/50 transition-colors" />
                </div>
              </div>
              <div className="mt-8 flex justify-end gap-3">
                <button onClick={() => setShowAddCam(false)} className="px-6 py-3 font-semibold text-slate-400 hover:text-white transition-colors">Cancel</button>
                <button onClick={() => startCamera(newCam.id, newCam.source)} className="btn-primary px-10">Initialize Connection</button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {loading ? (
        <div className="flex justify-center py-20">
          <LoadingSpinner label="Synchronizing Neural Networks..." />
        </div>
      ) : (
        <div className="grid gap-8 xl:grid-cols-3">
          {/* Feeds Grid */}
          <div className="xl:col-span-2 space-y-8">
            <div className="grid gap-8 md:grid-cols-2">
              {status.cameras.length > 0 ? (
                status.cameras.map((cam) => (
                  <LiveFeed key={cam.id} cameraId={cam.id} cameraRunning={cam.connected} onStop={stopCamera} />
                ))
              ) : (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="col-span-full glass-card h-[400px] flex flex-col items-center justify-center text-slate-500 border-dashed border-2 border-white/5 space-y-4">
                  <div className="p-5 rounded-full bg-white/5 text-slate-400"><IconVideo /></div>
                  <div className="text-center">
                    <p className="text-lg font-semibold text-slate-300">No active surveillance feeds</p>
                    <p className="text-sm">Add a CCTV link to begin real-time detection</p>
                  </div>
                  <button onClick={() => startCamera('Default_Cam', '0')} className="text-indigo-400 font-bold hover:text-indigo-300 transition-colors py-2 px-4 rounded-xl hover:bg-indigo-400/10">Start System Default Webcam</button>
                </motion.div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
            <StatusPanel status={status} />
            <AlertList alerts={alerts} onDelete={deleteAlert} />
          </div>
        </div>
      )}
    </div>
  )
}

export default DashboardPage
