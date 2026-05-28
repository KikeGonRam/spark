import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'
import Modal from '../../components/Modal'

export default function AdminAppointments() {
    const [appointments, setAppointments] = useState([])
    const [barbers, setBarbers] = useState([])
    const [services, setServices] = useState([])
    const [clients, setClients] = useState([])
    const [loading, setLoading] = useState(true)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [editingItem, setEditingItem] = useState(null)
    
    // Sincronizado con AppointmentCreate (FastAPI)
    const [formData, setFormData] = useState({
        barber_id: '',
        client_id: '',
        service_id: '',
        appointment_date: '',
        start_time: '',
        notes: ''
    })

    const loadData = async () => {
        setLoading(true)
        try {
            const [appRes, barbRes, servRes, clientRes] = await Promise.all([
                apiFetch('/appointments').then(r => r.json()),
                apiFetch('/barbers').then(r => r.json()),
                apiFetch('/services').then(r => r.json()),
                apiFetch('/clients').then(r => r.json())
            ])
            setAppointments(appRes.data?.appointments || [])
            setBarbers(barbRes.data?.barbers || [])
            setServices(servRes.data?.services || [])
            setClients(clientRes.data?.clients || [])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { loadData() }, [])

    const handleOpenModal = (app = null) => {
        if (app) {
            setEditingItem(app)
            setFormData({
                barber_id: app.barber_id || '',
                client_id: app.client_id || '',
                service_id: app.service_id || '',
                appointment_date: app.appointment_date || '',
                start_time: app.start_time || '',
                notes: app.notes || ''
            })
        } else {
            setEditingItem(null)
            setFormData({ barber_id: '', client_id: '', service_id: '', appointment_date: '', start_time: '', notes: '' })
        }
        setIsModalOpen(true)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        const method = editingItem ? 'PATCH' : 'POST'
        const url = editingItem ? `/appointments/${editingItem.id}` : '/appointments'
        
        try {
            const res = await apiFetch(url, {
                method,
                body: JSON.stringify(formData)
            })

            if (res.ok) {
                setIsModalOpen(false)
                loadData()
            } else {
                const err = await res.json()
                toast.error(err.detail || 'No se pudo agendar la cita')
            }
        } catch (error) {
            console.error("Error saving appointment", error)
        }
    }

    const handleDelete = async (id) => {
        if (!window.confirm('¿Cancelar esta cita premium?')) return
        await apiFetch(`/appointments/${id}`, { method: 'DELETE' })
        loadData()
    }

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Agenda de <span className="text-gold">Citas</span></h2>
                    <p className="ui-profile-subtitle">Control maestro de reservaciones</p>
                </div>
                <button onClick={() => handleOpenModal()} className="ui-btn-gold">+ Agendar Cita</button>
            </div>

            <section className="ui-card-premium">
                <div className="ui-table-premium-wrapper">
                <table className="ui-table-premium">
                    <thead>
                        <tr style={{ background: 'transparent' }}>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444' }}>CLIENTE</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444' }}>BARBERO</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444' }}>SERVICIO</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444' }}>FECHA/HORA</th>
                            <th style={{ textAlign: 'right', padding: '1rem', fontSize: '10px', color: '#444' }}>ACCIONES</th>
                        </tr>
                    </thead>
                    <tbody>
                        {appointments.map((a, i) => (
                            <tr key={a.id ?? i}>
                                <td><div style={{ fontWeight: 800 }}>{a.client_name || 'Invitado'}</div></td>
                                <td><div style={{ fontSize: '13px' }}>{a.barber_name || 'Por asignar'}</div></td>
                                <td><div style={{ color: 'var(--gold)', fontWeight: 700 }}>{a.service_name || 'Corte'}</div></td>
                                <td>
                                    <div style={{ fontSize: '12px' }}>{a.appointment_date}</div>
                                    <div style={{ fontSize: '10px', color: '#555' }}>{a.start_time}</div>
                                </td>
                                <td style={{ textAlign: 'right' }}>
                                    <button onClick={() => handleOpenModal(a)} className="ui-btn" style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.03)', marginRight: '8px' }}>Editar</button>
                                    <button onClick={() => handleDelete(a.id)} className="ui-btn" style={{ padding: '6px 12px', color: '#f87171' }}>Cancelar</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {loading && <p className="text-center py-12 text-muted animate-pulse">Sincronizando agenda...</p>}
                </div>
            </section>

            <Modal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)}
                title={editingItem ? 'Reprogramar Cita' : 'Nueva Cita Premium'}
                actions={
                    <>
                        <button onClick={() => setIsModalOpen(false)} className="ui-btn" style={{ background: 'transparent' }}>Cerrar</button>
                        <button onClick={handleSubmit} className="ui-btn-gold">Confirmar Cita</button>
                    </>
                }
            >
                <form className="space-y-4">
                    <div className="group">
                        <label className="ui-kpi-label">Cliente</label>
                        <select className="ui-input" required value={formData.client_id} onChange={e => setFormData({...formData, client_id: e.target.value})}>
                            <option value="">Seleccionar Caballero...</option>
                            {clients.map(c => <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>)}
                        </select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="group">
                            <label className="ui-kpi-label">Barbero</label>
                            <select className="ui-input" required value={formData.barber_id} onChange={e => setFormData({...formData, barber_id: e.target.value})}>
                                <option value="">Seleccionar Maestro...</option>
                                {barbers.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                            </select>
                        </div>
                        <div className="group">
                            <label className="ui-kpi-label">Servicio</label>
                            <select className="ui-input" required value={formData.service_id} onChange={e => setFormData({...formData, service_id: e.target.value})}>
                                <option value="">Seleccionar Ritual...</option>
                                {services.map(s => <option key={s.id} value={s.id}>{s.name || s.nombre}</option>)}
                            </select>
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="group">
                            <label className="ui-kpi-label">Fecha</label>
                            <input type="date" className="ui-input" required value={formData.appointment_date} onChange={e => setFormData({...formData, appointment_date: e.target.value})} />
                        </div>
                        <div className="group">
                            <label className="ui-kpi-label">Hora (HH:MM)</label>
                            <input type="time" className="ui-input" required value={formData.start_time} onChange={e => setFormData({...formData, start_time: e.target.value})} />
                        </div>
                    </div>
                    <div className="group">
                        <label className="ui-kpi-label">Notas</label>
                        <textarea 
                            className="ui-input" 
                            value={formData.notes} 
                            onChange={e => setFormData({...formData, notes: e.target.value})}
                            placeholder="Preferencias especiales..."
                            style={{ minHeight: '60px', resize: 'none' }}
                        />
                    </div>
                </form>
            </Modal>
        </div>
    )
}
