import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { API_BASE_URL, api } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

function EvidencePage() {
  const [evidence, setEvidence] = useState([])
  const [loading, setLoading] = useState(true)
  const [severity, setSeverity] = useState('')
  const [date, setDate] = useState('')

  const fetchEvidence = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/evidence', { params: { severity: severity || undefined, date: date || undefined } })
      setEvidence(data.evidence || [])
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to fetch evidence')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvidence()
  }, [severity, date])

  const token = useMemo(() => localStorage.getItem('vg_token'), [])

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Evidence Management</h1>
      <div className="glass flex flex-wrap items-center gap-3 rounded-2xl p-4">
        <select className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm" value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="">All Severities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
        </select>
        <input className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>

      {loading ? <LoadingSpinner label="Loading evidence..." /> : null}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {evidence.map((item) => (
          <article key={item.id} className="glass rounded-2xl p-4">
            <p className="font-medium">{item.activity_type}</p>
            <p className="text-sm text-slate-300">{new Date(item.timestamp).toLocaleString()}</p>
            <p className="text-sm text-slate-300">Confidence: {(item.confidence * 100).toFixed(0)}%</p>
            <span className={`mt-2 inline-block rounded px-2 py-1 text-xs ${item.severity === 'high' ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'}`}>
              {item.severity}
            </span>
            {item.clip ? (
              <div className="mt-3 space-y-2">
                <video controls className="w-full rounded-lg border border-white/10" src={`${API_BASE_URL}/api/evidence/${item.clip}?token=${token}`} />
                <a className="inline-block rounded-lg bg-cyan-500 px-3 py-2 text-sm font-semibold text-slate-900" href={`${API_BASE_URL}${item.download_url}?token=${token}&download=1`}>
                  Download Clip
                </a>
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </div>
  )
}

export default EvidencePage
