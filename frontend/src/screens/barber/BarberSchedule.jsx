import { useState, useEffect } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'
import { Badge } from '../../components/UI'
import Modal from '../../components/Modal'

export default function BarberSchedule() {
    const [appointments, setAppointments] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedApp, setSelectedApp] = useState(null)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [formData, setFormData] = useState({ status: '', notes: '', feedback: '' })

    const load = async () => {
        setLoading(true)
        try {
            // En producción aquí filtraríamos por barber_id del usuario logueado
            const res = await apiFetch('/appointments')
            const data = await res.json()
            setAppointments(data.data?.appointments || [])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [])

    const handleOpenModal = (app) => {
        setSelectedApp(app)
        setFormData({
            status: app.status || 'pending',
            notes: app.notes || '',
            feedback: app.feedback || ''
        })
        setIsModalOpen(true)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        // Sincronizado con AppointmentUpdate (FastAPI)
        const res = await apiFetch(`/appointments/${selectedApp.id}`, {
            method: 'PATCH',
            body: JSON.stringify(formData)
        })

        if (res.ok) {
            setIsModalOpen(false)
            load()
        } else {
            const err = await res.json()
            toast.error(err.detail || 'No se pudo actualizar la cita')
        }
    }

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Mi <span className="text-gold">Agenda</span></h2>
                    <p className="ui-profile-subtitle">Gestiona tus servicios del día</p>
                </div>
                <Badge className="bg-white/5 border-white/10">Hoy: {new Date().toLocaleDateString()}</Badge>
            </div>

            <section className="ui-card-premium">
                <table className="ui-table-premium">
                    <thead>
                        <tr style={{ background: 'transparent' }}>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444' }}>HORA</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444' }}>CLIENTE</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444' }}>SERVICIO</th>
                            <th style={{ textAlign: 'right', padding: '1rem', fontSize: '10px', color: '#444' }}>ESTADO</th>
                        </tr>
                    </thead>
                    <tbody>
                        {appointments.map((a) => (
                            <tr key={a.id} onClick={() => handleOpenModal(a)} style={{ cursor: 'pointer' }}>
                                <td style={{ fontWeight: 900, color: 'var(--gold)' }}>{a.start_time}</td>
                                <td>
                                    <div style={{ fontWeight: 800 }}>{a.client_name || 'Caballero'}</div>
                                    <div style={{ fontSize: '10px', color: '#555' }}>{a.notes ? 'Ver notas...' : 'Sin observaciones'}</div>
                                </td>
                                <td>{a.service_name || 'Corte'}</td>
                                <td style={{ textAlign: 'right' }}>
                                    <Badge className={
                                        a.status === 'completed' ? 'text-green-400 border-green-500/20' : 
                                        a.status === 'cancelled' ? 'text-red-400 border-red-500/20' : ''
                                    }>
                                        {a.status || 'Pendiente'}
                                    </Badge>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {loading && <p className="text-center py-12 text-muted animate-pulse">Sincronizando agenda...</p>}
                {!loading && appointments.length === 0 && <p className="text-center py-12 text-muted">No hay citas para mostrar.</p>}
            </section>

            <Modal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)}
                title="Gestionar Servicio"
                actions={
                    <>
                        <button onClick={() => setIsModalOpen(false)} className="ui-btn" style={{ background: 'transparent' }}>Cerrar</button>
                        <button onClick={handleSubmit} className="ui-btn-gold">Guardar Cambios</button>
                    </>
                }
            >
                <form className="space-y-4">
                    <div className="group">
                        <label className="ui-kpi-label">Estado del Servicio</label>
                        <select 
                            className="ui-input mt-2" 
                            value={formData.status} 
                            onChange={e => setFormData({...formData, status: e.target.value})}
                        >
                            <option value="pending">Pendiente</option>
                            <option value="confirmed">Confirmado</option>
                            <option value="in_progress">En Curso</option>
                            <option value="completed">Completado</option>
                            <option value="cancelled">Cancelado</option>
                            <option value="no_show">No se presentó</option>
                        </select>
                    </div>
                    <div className="group">
                        <label className="ui-kpi-label">Notas del Cliente</label>
                        <textarea 
                            className="ui-input mt-2" 
                            value={formData.notes} 
                            onChange={e => setFormData({...formData, notes: e.target.value})}
                            style={{ minHeight: '60px', opacity: 0.6 }}
                            placeholder="Notas de la reservación..."
                        />
                    </div>
                    <div className="group">
                        <label className="ui-kpi-label">Observaciones del Barbero</label>
                        <textarea 
                            className="ui-input mt-2" 
                            value={formData.feedback} 
                            onChange={e => setFormData({...formData, feedback: e.target.value})}
                            style={{ minHeight: '80px' }}
                            placeholder="Ej: El cliente prefiere corte bajo en los laterales..."
                        />
                    </div>
                </form>
            </Modal>
        </div>
    )
}
