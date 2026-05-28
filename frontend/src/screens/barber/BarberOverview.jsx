import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { Badge } from '../../components/UI'

export default function BarberOverview({ summary, health }) {
    const [appointments, setAppointments] = useState([])
    const [loading, setLoading] = useState(true)
    const [stats, setStats] = useState({ today: 0, completed: 0, revenue: 0, rating: null })

    useEffect(() => {
        const load = async () => {
            try {
                const today = new Date().toISOString().slice(0, 10)
                const res = await apiFetch(`/appointments?start_date=${today}&end_date=${today}`)
                const data = await res.json()
                const apps = data.data?.appointments || data.data || []
                setAppointments(apps)
                const completed = apps.filter(a => a.status === 'completed').length
                setStats({
                    today: apps.length,
                    completed,
                    revenue: apps.filter(a => a.status === 'completed').reduce((s, a) => s + (a.service_price || 0), 0),
                    rating: null
                })
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [])

    const now = new Date()
    const nowStr = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`
    const nextApp = appointments
        .filter(a => a.status !== 'completed' && a.status !== 'cancelled' && a.start_time >= nowStr)
        .sort((a, b) => a.start_time.localeCompare(b.start_time))[0]

    return (
        <div className="space-y-8 animate-fade-in">
            <div>
                <h2 className="ui-profile-title">¡Hola, <span className="text-gold">Maestro</span>!</h2>
                <p className="ui-profile-subtitle">Tu maestría define nuestro estándar hoy.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="ui-kpi-card"><p className="ui-kpi-label">Citas Hoy</p><p className="ui-kpi-value">{loading ? '...' : stats.today}</p></div>
                <div className="ui-kpi-card"><p className="ui-kpi-label">Completadas</p><p className="ui-kpi-value" style={{ color: '#4ade80' }}>{loading ? '...' : stats.completed}</p></div>
                <div className="ui-kpi-card"><p className="ui-kpi-label">Ingresos Día</p><p className="ui-kpi-value" style={{ color: 'var(--gold)' }}>{loading ? '...' : `$${stats.revenue}`}</p></div>
                <div className="ui-kpi-card"><p className="ui-kpi-label">Rating</p><p className="ui-kpi-value" style={{ color: '#a78bfa' }}>—</p></div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <section className="ui-card-premium">
                    <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem' }}>Siguiente Cliente</h3>
                    {nextApp ? (
                        <div style={{ padding: '1rem', background: 'rgba(212,175,55,0.05)', border: '1px solid rgba(212,175,55,0.2)', borderRadius: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <p style={{ fontSize: '14px', fontWeight: 900 }}>{nextApp.client_name || 'Cliente'}</p>
                                <p style={{ fontSize: '10px', color: 'var(--gold)', fontWeight: 800, textTransform: 'uppercase' }}>{nextApp.service_name || 'Servicio'}</p>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <p style={{ fontSize: '20px', fontWeight: 900 }}>{nextApp.start_time?.slice(0, 5)}</p>
                                <Badge>Próxima</Badge>
                            </div>
                        </div>
                    ) : (
                        <p style={{ color: 'var(--muted)', fontSize: '12px' }}>No hay más citas pendientes hoy.</p>
                    )}
                </section>

                <section className="ui-card-premium">
                    <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem' }}>Citas del Día</h3>
                    {loading && <p style={{ color: 'var(--muted)', fontSize: '12px' }} className="animate-pulse">Cargando...</p>}
                    {!loading && appointments.length === 0 && <p style={{ color: 'var(--muted)', fontSize: '12px' }}>Sin citas para hoy.</p>}
                    <div className="space-y-2">
                        {appointments.slice(0, 5).map(a => (
                            <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.6rem 0.75rem', background: 'rgba(255,255,255,0.02)', borderRadius: '0.5rem' }}>
                                <span style={{ fontSize: '12px', fontWeight: 800 }}>{a.start_time?.slice(0, 5)} — {a.client_name || 'Cliente'}</span>
                                <span style={{ fontSize: '9px', fontWeight: 900, color: a.status === 'completed' ? '#4ade80' : a.status === 'cancelled' ? '#f87171' : 'var(--gold)', textTransform: 'uppercase' }}>{a.status}</span>
                            </div>
                        ))}
                    </div>
                </section>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#4ade80' }} className="animate-pulse" />
                <p style={{ fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', color: '#4ade80' }}>{health}</p>
            </div>
        </div>
    )
}
