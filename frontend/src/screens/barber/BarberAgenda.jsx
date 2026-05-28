import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'

const STATUS_COLORS = {
    pending: '#facc15', confirmed: '#60a5fa',
    in_progress: 'var(--gold)', completed: '#4ade80',
    cancelled: '#f87171', no_show: '#a78bfa'
}
const STATUS_LABELS = {
    pending: 'Pendiente', confirmed: 'Confirmada',
    in_progress: 'En proceso', completed: 'Completada',
    cancelled: 'Cancelada', no_show: 'No asistió'
}

function getDaysOfWeek(baseDate) {
    const monday = new Date(baseDate)
    monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7))
    return Array.from({ length: 7 }, (_, i) => {
        const d = new Date(monday)
        d.setDate(monday.getDate() + i)
        return d
    })
}

const pad = n => String(n).padStart(2, '0')
const fmt = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const DAY_NAMES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

export default function BarberAgenda() {
    const [appointments, setAppointments] = useState([])
    const [loading, setLoading] = useState(true)
    const [currentWeek, setCurrentWeek] = useState(new Date())
    const [selectedDate, setSelectedDate] = useState(fmt(new Date()))

    const days = getDaysOfWeek(currentWeek)

    const load = async () => {
        setLoading(true)
        try {
            const start = fmt(days[0])
            const end = fmt(days[6])
            const res = await apiFetch(`/appointments?start_date=${start}&end_date=${end}`)
            const data = await res.json()
            setAppointments(data.data?.appointments || data.data || [])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [currentWeek])

    const byDate = (date) => appointments.filter(a => a.appointment_date === date)
    const selectedApps = byDate(selectedDate)

    const prevWeek = () => {
        const d = new Date(currentWeek)
        d.setDate(d.getDate() - 7)
        setCurrentWeek(d)
    }
    const nextWeek = () => {
        const d = new Date(currentWeek)
        d.setDate(d.getDate() + 7)
        setCurrentWeek(d)
    }

    const updateStatus = async (id, status) => {
        await apiFetch(`/appointments/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) })
        load()
    }

    const monthYear = days[0].toLocaleDateString('es-MX', { month: 'long', year: 'numeric' })

    return (
        <div className="space-y-8 animate-fade-in">
            <div>
                <h2 className="ui-profile-title">Mi <span className="text-gold">Agenda</span></h2>
                <p className="ui-profile-subtitle">Calendario semanal de citas</p>
            </div>

            {/* Week Navigator */}
            <section className="ui-card-premium">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                    <button onClick={prevWeek} style={{ background: 'transparent', border: '1px solid var(--line)', color: '#fff', padding: '6px 14px', borderRadius: '0.5rem', cursor: 'pointer', fontSize: '14px' }}>‹</button>
                    <h3 style={{ fontSize: '12px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--gold)' }}>{monthYear}</h3>
                    <button onClick={nextWeek} style={{ background: 'transparent', border: '1px solid var(--line)', color: '#fff', padding: '6px 14px', borderRadius: '0.5rem', cursor: 'pointer', fontSize: '14px' }}>›</button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '8px' }}>
                    {days.map((day, i) => {
                        const dateStr = fmt(day)
                        const count = byDate(dateStr).length
                        const isSelected = dateStr === selectedDate
                        const isToday = dateStr === fmt(new Date())
                        return (
                            <button key={i} onClick={() => setSelectedDate(dateStr)} style={{ padding: '0.75rem 0.25rem', borderRadius: '0.75rem', cursor: 'pointer', border: isSelected ? '1px solid var(--gold)' : isToday ? '1px solid rgba(212,175,55,0.3)' : '1px solid var(--line)', background: isSelected ? 'rgba(212,175,55,0.1)' : 'transparent', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', transition: 'all 0.2s' }}>
                                <span style={{ fontSize: '8px', fontWeight: 900, color: 'var(--muted)', textTransform: 'uppercase' }}>{DAY_NAMES[i]}</span>
                                <span style={{ fontSize: '18px', fontWeight: 900, color: isSelected ? 'var(--gold)' : isToday ? '#fff' : '#666' }}>{day.getDate()}</span>
                                {count > 0 && (
                                    <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: isSelected ? 'var(--gold)' : 'rgba(255,255,255,0.08)', display: 'grid', placeItems: 'center' }}>
                                        <span style={{ fontSize: '9px', fontWeight: 900, color: isSelected ? '#000' : '#fff' }}>{count}</span>
                                    </div>
                                )}
                            </button>
                        )
                    })}
                </div>
            </section>

            {/* Day Appointments */}
            <section>
                <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.25rem', color: 'var(--muted)' }}>
                    {new Date(selectedDate + 'T12:00:00').toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long' })} — {selectedApps.length} cita(s)
                </h3>

                {loading && <p className="text-center py-8 text-muted animate-pulse">Cargando citas...</p>}

                {!loading && selectedApps.length === 0 && (
                    <div className="ui-card-premium text-center" style={{ padding: '3rem' }}>
                        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📅</div>
                        <p style={{ color: 'var(--muted)', fontSize: '13px' }}>Sin citas programadas para este día</p>
                    </div>
                )}

                <div className="space-y-3">
                    {selectedApps.sort((a, b) => (a.start_time || '').localeCompare(b.start_time || '')).map(app => (
                        <div key={app.id} className="ui-card-premium" style={{ padding: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', borderLeft: `3px solid ${STATUS_COLORS[app.status] || '#444'}` }}>
                            <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center', flex: 1 }}>
                                <div style={{ textAlign: 'center', minWidth: '50px' }}>
                                    <p style={{ fontSize: '18px', fontWeight: 900, color: 'var(--gold)' }}>{app.start_time?.slice(0, 5) || '--:--'}</p>
                                    <p style={{ fontSize: '9px', color: '#555' }}>{app.end_time?.slice(0, 5) || ''}</p>
                                </div>
                                <div>
                                    <p style={{ fontWeight: 900, fontSize: '14px' }}>{app.client_name || 'Cliente'}</p>
                                    <p style={{ fontSize: '11px', color: 'var(--gold)', fontWeight: 700 }}>{app.service_name || 'Servicio'}</p>
                                    {app.notes && <p style={{ fontSize: '10px', color: '#666', marginTop: '2px' }}>{app.notes}</p>}
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                <span style={{ fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', color: STATUS_COLORS[app.status], background: `${STATUS_COLORS[app.status]}18`, padding: '3px 8px', borderRadius: '99px' }}>
                                    {STATUS_LABELS[app.status] || app.status}
                                </span>
                                {app.status === 'confirmed' && (
                                    <button onClick={() => updateStatus(app.id, 'in_progress')} className="ui-btn-gold" style={{ padding: '5px 10px', fontSize: '9px' }}>Iniciar</button>
                                )}
                                {app.status === 'in_progress' && (
                                    <button onClick={() => updateStatus(app.id, 'completed')} className="ui-btn-gold" style={{ padding: '5px 10px', fontSize: '9px' }}>Completar</button>
                                )}
                                {(app.status === 'pending' || app.status === 'confirmed') && (
                                    <button onClick={() => updateStatus(app.id, 'cancelled')} className="ui-btn" style={{ padding: '5px 10px', fontSize: '9px', color: '#f87171', background: 'rgba(248,113,113,0.08)' }}>Cancelar</button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    )
}
