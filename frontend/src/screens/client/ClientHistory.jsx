import { useState, useEffect } from 'react'
import { apiFetch, navigate, getStoredUser } from '../../hooks/useNavigation'
import { Badge } from '../../components/UI'

export default function ClientHistory() {
    const [appointments, setAppointments] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const load = async () => {
            try {
                const stored = getStoredUser()
                if (!stored || stored.role !== 'client') {
                    setAppointments([])
                    return
                }
                const res = await apiFetch('/appointments')
                const data = await res.json()
                setAppointments(data.data?.appointments || [])
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [])

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Mi <span className="text-gold">Historial</span></h2>
                    <p className="ui-profile-subtitle">Tus visitas pasadas y próximas citas</p>
                </div>
                <button onClick={() => navigate('/dashboard/client/booking')} className="ui-btn-gold">Nueva Reserva</button>
            </div>

            <section className="ui-card-premium">
                <table className="ui-table-premium">
                    <thead>
                        <tr style={{ background: 'transparent' }}>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444' }}>FECHA</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444' }}>SERVICIO</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444' }}>BARBERO</th>
                            <th style={{ textAlign: 'right', padding: '1rem', fontSize: '10px', color: '#444' }}>ESTADO</th>
                        </tr>
                    </thead>
                    <tbody>
                        {appointments.map((a) => (
                            <tr key={a.id}>
                                <td style={{ fontWeight: 800 }}>{a.appointment_date}</td>
                                <td style={{ color: 'var(--gold)', fontWeight: 700 }}>{a.service_name || 'Corte Signature'}</td>
                                <td>{a.barber_name || 'Maestro Senior'}</td>
                                <td style={{ textAlign: 'right' }}>
                                    <Badge className={a.status === 'completed' ? 'text-green-400 border-green-500/20' : ''}>
                                        {a.status || 'Pendiente'}
                                    </Badge>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {loading && <p className="text-center py-12 text-muted animate-pulse">Sincronizando historial...</p>}
                {!loading && appointments.length === 0 && (
                    <div className="text-center py-12">
                        <p className="text-muted">Aún no tienes servicios registrados.</p>
                    </div>
                )}
            </section>
        </div>
    )
}
