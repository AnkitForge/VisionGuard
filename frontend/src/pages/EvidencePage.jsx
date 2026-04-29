import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { API_BASE_URL, api } from '../services/api'
import { useAuth } from '../context/AuthContext'
import LoadingSpinner from '../components/LoadingSpinner'

// Icons
const IconSearch = () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
const IconDownload = () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
const IconTrash = () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>

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

  const handleDelete = async (id) => {
    if (!window.confirm('This action will permanently delete this evidence. Proceed?')) return
    try {
      await api.delete(`/alerts/${id}`)
      toast.success('Evidence purged successfully')
      setEvidence((prev) => prev.filter((item) => item.id !== id))
    } catch (err) {
      toast.error('Purge failed')
    }
  }

  useEffect(() => {
    fetchEvidence()
  }, [severity, date])

  const { token } = useAuth()

  return (
    <div className="max-w-[1600px] mx-auto space-y-8 pb-10">
      <div className="flex flex-wrap items-end justify-between gap-6 border-b border-white/5 pb-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gradient">Evidence Vault</h1>
          <p className="text-slate-400 font-medium mt-1">Archived intelligence and incident recordings</p>
        </div>
        <div className="flex items-center gap-4 bg-slate-900/40 p-2 rounded-2xl border border-white/5 backdrop-blur-md">
          <div className="relative">
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"><IconSearch /></div>
            <select className="bg-black/40 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm outline-none focus:border-indigo-500/50 appearance-none min-w-[160px]" value={severity} onChange={(e) => setSeverity(e.target.value)}>
              <option value="">All Priorities</option>
              <option value="high">High Priority</option>
              <option value="medium">Standard</option>
            </select>
          </div>
          <input className="bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-sm outline-none focus:border-indigo-500/50" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </div>
      </div>

      {loading ? (
        <div className="py-20"><LoadingSpinner label="Decrypting Archives..." /></div>
      ) : evidence.length === 0 ? (
        <div className="py-32 text-center glass-card border-dashed border-2 border-white/5">
          <p className="text-slate-500 font-medium">No archived incidents found matching filters.</p>
        </div>
      ) : (
        <div className="grid gap-8 md:grid-cols-2 xl:grid-cols-3">
          {evidence.map((item) => (
            <article key={item.id} className="glass-card flex flex-col group">
              <div className="p-5 flex items-center justify-between border-b border-white/5 bg-white/[0.02]">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${item.severity === 'high' ? 'bg-rose-500' : 'bg-amber-500'}`} />
                  <p className="text-sm font-bold uppercase tracking-widest text-slate-300">{item.activity_type}</p>
                </div>
                <span className={`text-[10px] font-black px-2 py-0.5 rounded-md uppercase tracking-widest ${item.severity === 'high' ? 'bg-rose-500/10 text-rose-400' : 'bg-amber-500/10 text-amber-400'}`}>
                  {item.severity}
                </span>
              </div>
              
              <div className="aspect-video bg-black/40 overflow-hidden">
                 <video controls className="w-full h-full object-contain" src={`${API_BASE_URL}/api/evidence/${item.clip}?token=${token}`} />
              </div>

              <div className="p-5 space-y-4 flex-1 flex flex-col">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Timestamp</p>
                    <p className="text-xs font-semibold text-slate-300 mt-1">{new Date(item.timestamp).toLocaleString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Confidence</p>
                    <p className="text-xs font-black text-indigo-400 mt-1">{(item.confidence * 100).toFixed(0)}%</p>
                  </div>
                </div>

                <div className="pt-4 mt-auto flex gap-3">
                  <a className="flex-1 btn-secondary justify-center text-xs py-2.5" href={`${API_BASE_URL}${item.download_url}?token=${token}&download=1`}>
                    <IconDownload />
                    Download
                  </a>
                  <button onClick={() => handleDelete(item.id)} className="px-4 py-2.5 rounded-2xl bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-all">
                    <IconTrash />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}

export default EvidencePage
