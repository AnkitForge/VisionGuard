import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
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

function DashboardPage() {
  const [status, setStatus] = useState({ camera_connected: false, model_running: false, processing_fps: 0, total_alerts_today: 0 })
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [popupAlert, setPopupAlert] = useState(null)
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

      <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <LiveFeed cameraRunning={status.camera_connected && status.model_running} />
        <StatusPanel status={status} />
      </div>

      <AlertList alerts={alerts} />
    </div>
  )
}

export default DashboardPage
