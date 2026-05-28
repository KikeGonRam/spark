import { useEffect, useState } from 'react'
import AdminOverview from './admin/AdminOverview'
import AdminServices from './admin/AdminServices'
import AdminAppointments from './admin/AdminAppointments'
import AdminClients from './admin/AdminClients'
import AdminBarbers from './admin/AdminBarbers'
import AdminUsers from './admin/AdminUsers'
import AdminPayments from './admin/AdminPayments'
import AdminInventory from './admin/AdminInventory'
import AdminReports from './admin/AdminReports'
import AdminPredictions from './admin/AdminPredictions'
import AdminSettings from './admin/AdminSettings'
import AdminLogs from './admin/AdminLogs'

import BarberOverview from './barber/BarberOverview'
import BarberAgenda from './barber/BarberAgenda'
import BarberSchedule from './barber/BarberSchedule'
import BarberPortfolio from './barber/BarberPortfolio'
import BarberProfile from './barber/BarberProfile'

import ClientOverview from './client/ClientOverview'
import ClientBooking from './client/ClientBooking'
import ClientHistory from './client/ClientHistory'
import ClientNotifications from './client/ClientNotifications'
import ClientProfile from './client/ClientProfile'

import DashboardLayout from '../layouts/DashboardLayout'
import { apiFetch } from '../hooks/useNavigation'

export default function DashboardScreen({ role, subview }) {
  const [health, setHealth] = useState('Cargando...')
  const [summary, setSummary] = useState(null)

  const refresh = async () => {
    try {
      const [h, s] = await Promise.all([
        fetch('/health').then(r => r.json()),
        apiFetch('/dashboard/summary').then(r => r.json())
      ])
      setHealth(`Backend ${h.status}`)
      setSummary(s.data)
    } catch {
      setHealth('Desconectado')
    }
  }

  useEffect(() => { refresh() }, [])

  const renderSubview = () => {
    // --- ADMIN ---
    if (role === 'Administrativo') {
      switch (subview) {
        case 'services':     return <AdminServices />
        case 'appointments': return <AdminAppointments />
        case 'clients':      return <AdminClients />
        case 'barbers':      return <AdminBarbers />
        case 'users':        return <AdminUsers />
        case 'payments':     return <AdminPayments />
        case 'inventory':    return <AdminInventory />
        case 'reports':      return <AdminReports />
        case 'predictions':  return <AdminPredictions />
        case 'settings':     return <AdminSettings />
        case 'logs':         return <AdminLogs />
        case 'overview':
        default:             return <AdminOverview summary={summary} health={health} />
      }
    }

    // --- BARBER ---
    if (role === 'Profesional') {
      switch (subview) {
        case 'agenda':    return <BarberAgenda />
        case 'schedule':  return <BarberSchedule />
        case 'portfolio': return <BarberPortfolio />
        case 'profile':   return <BarberProfile />
        case 'overview':
        default:          return <BarberOverview summary={summary} health={health} />
      }
    }

    // --- CLIENT ---
    if (role === 'Cliente') {
      switch (subview) {
        case 'booking':       return <ClientBooking />
        case 'history':       return <ClientHistory />
        case 'notifications': return <ClientNotifications />
        case 'profile':       return <ClientProfile />
        case 'overview':
        default:              return <ClientOverview summary={summary} health={health} />
      }
    }

    return <div className="p-8"><h1 className="ui-profile-title">Vista no encontrada</h1></div>
  }

  return (
    <DashboardLayout role={role} subview={subview}>
      {renderSubview()}
    </DashboardLayout>
  )
}
