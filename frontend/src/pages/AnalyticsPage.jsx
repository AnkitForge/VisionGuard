import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { api } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

// Icons
const IconActivity = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
const IconTarget = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
const IconShield = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>

const COLORS = ['#6366f1', '#f43f5e', '#f59e0b', '#10b981']

function AnalyticsPage() {
  const [loading, setLoading] = useState(true)
  const [analytics, setAnalytics] = useState({ alerts_per_day: [], threat_distribution: [], detection_accuracy: 0, total_alerts: 0 })

  useEffect(() => {
    ;(async () => {
      setLoading(true)
      try {
        const { data } = await api.get('/analytics')
        setAnalytics(data)
      } catch (err) {
        toast.error(err.response?.data?.error || 'Failed to fetch analytics')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  return (
    <div className="max-w-[1600px] mx-auto space-y-8 pb-10">
      <div className="border-b border-white/5 pb-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-gradient">System Intelligence</h1>
        <p className="text-slate-400 font-medium mt-1">Neural network performance and threat distribution analytics</p>
      </div>

      {loading ? (
        <div className="py-20"><LoadingSpinner label="Compiling Data Streams..." /></div>
      ) : (
        <>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="glass-card p-6 flex items-center gap-5">
              <div className="p-4 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"><IconTarget /></div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Avg. Precision</p>
                <p className="text-3xl font-black text-white">{analytics?.detection_accuracy ?? 0}%</p>
              </div>
            </div>
            <div className="glass-card p-6 flex items-center gap-5">
              <div className="p-4 rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/20"><IconActivity /></div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Total Encounters</p>
                <p className="text-3xl font-black text-white">{analytics?.total_alerts ?? 0}</p>
              </div>
            </div>
            <div className="glass-card p-6 flex items-center gap-5">
              <div className="p-4 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><IconShield /></div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">System Integrity</p>
                <p className="text-3xl font-black text-white">99.4%</p>
              </div>
            </div>
          </div>

          <div className="grid gap-8 xl:grid-cols-2">
            <section className="glass-card p-8">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-xl font-bold text-white">Threat Activity Timeline</h2>
                <div className="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-[10px] font-bold tracking-widest uppercase">Real-time Data</div>
              </div>
              <div className="h-[350px]">
                {analytics?.alerts_per_day?.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={analytics.alerts_per_day} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                      <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dy={10} />
                      <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dx={-10} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)' }}
                        itemStyle={{ color: '#818cf8', fontWeight: '800', fontSize: '12px' }}
                        labelStyle={{ color: '#f8fafc', marginBottom: '4px', fontWeight: 'bold' }}
                      />
                      <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={4} dot={{ fill: '#6366f1', strokeWidth: 2, r: 4 }} activeDot={{ r: 8, strokeWidth: 0, fill: '#818cf8' }} animationDuration={2000} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-500 text-sm font-medium border border-dashed border-white/5 rounded-3xl">
                    No threat activity recorded yet.
                  </div>
                )}
              </div>
            </section>

            <section className="glass-card p-8">
               <div className="flex items-center justify-between mb-8">
                <h2 className="text-xl font-bold text-white">Category Distribution</h2>
                <div className="flex flex-wrap gap-3">
                   {analytics?.threat_distribution?.map((d, i) => (
                     <div key={d.name} className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5">
                        <div className="w-2 h-2 rounded-full shadow-[0_0_8px_rgba(255,255,255,0.2)]" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                        <span className="text-[10px] text-slate-300 uppercase font-black tracking-widest">{d.name}</span>
                     </div>
                   ))}
                </div>
              </div>
              <div className="h-[350px]">
                {analytics?.threat_distribution?.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={analytics.threat_distribution} dataKey="value" nameKey="name" innerRadius={80} outerRadius={120} paddingAngle={8}>
                        {analytics.threat_distribution.map((entry, index) => (
                          <Cell key={entry.name} fill={COLORS[index % COLORS.length]} stroke="rgba(255,255,255,0.05)" strokeWidth={2} />
                        ))}
                      </Pie>
                      <Tooltip 
                         contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px' }}
                         labelStyle={{ display: 'none' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                   <div className="h-full flex items-center justify-center text-slate-500 text-sm font-medium border border-dashed border-white/5 rounded-3xl">
                    Insufficient data for distribution.
                  </div>
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  )
}

export default AnalyticsPage
