import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'

function DashboardLayout() {
  return (
    <div className="min-h-screen md:flex">
      <Sidebar />
      <main className="flex-1 p-4 md:p-6">
        <Outlet />
      </main>
    </div>
  )
}

export default DashboardLayout
