// Import React hooks for managing component state and lifecycle
import { useEffect, useState } from 'react'
// Import toast notifications for error messages
import toast from 'react-hot-toast'
// Import chart components from recharts for analytics visualization
import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
// Import API instance (Axios or similar) for backend communication
import { api } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
// Color palette used for pie chart segments
const COLORS = ['#22d3ee', '#fb7185', '#f59e0b', '#34d399']

function AnalyticsPage() {
  const [loading, setLoading] = useState(true)
  const [analytics, setAnalytics] = useState({ alerts_per_day: [], threat_distribution: [], detection_accuracy: 0, total_alerts: 0 })
  // useEffect runs once when the component loads

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
  }, [])// empty dependency array → runs only once on page load

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Analytics & Insights</h1>
      {loading ? <LoadingSpinner label="Loading analytics..." /> : null}

      <div className="grid gap-4 md:grid-cols-3">
        <div className="glass rounded-2xl p-4">
          <p className="text-sm text-slate-400">Detection Accuracy</p>
          <p className="text-3xl font-semibold text-cyan-300">{analytics.detection_accuracy}%</p>
        </div>
        <div className="glass rounded-2xl p-4">
          <p className="text-sm text-slate-400">Total Alerts</p>
          <p className="text-3xl font-semibold text-cyan-300">{analytics.total_alerts}</p>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <section className="glass rounded-2xl p-4">
          <h2 className="mb-3 text-lg font-semibold">Alerts Per Day</h2>
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics.alerts_per_day}>
                <CartesianGrid stroke="rgba(255,255,255,0.15)" strokeDasharray="3 3" />
                <XAxis dataKey="date" stroke="#cbd5e1" />
                <YAxis stroke="#cbd5e1" />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#22d3ee" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="glass rounded-2xl p-4">
          <h2 className="mb-3 text-lg font-semibold">Threat Distribution</h2>
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={analytics.threat_distribution} dataKey="value" nameKey="name" outerRadius={110}>
                  {analytics.threat_distribution.map((entry, index) => (
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>
    </div>
  )
}

export default AnalyticsPage
