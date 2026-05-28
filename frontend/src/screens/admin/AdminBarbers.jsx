import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'
import Modal from '../../components/Modal'

const DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

export default function AdminBarbers() {
    const [barbers, setBarbers] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedBarber, setSelectedBarber] = useState(null)
    const [isEditModal, setIsEditModal] = useState(false)
    const [isScheduleModal, setIsScheduleModal] = useState(false)

    const [formData, setFormData] = useState({
        name: '', specialization: '', bio: '', is_available: true
    })
    const [schedule, setSchedule] = useState(
        DAYS.map((day, i) => ({ day_of_week: i, is_working: i < 6, start_time: '09:00', end_time: '19:00' }))
    )

    const load = async () => {
        setLoading(true)
        try {
            const res = await apiFetch('/barbers')
            const data = await res.json()
            setBarbers(data.data?.barbers || data.data || [])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [])

    const openEditModal = (b) => {
        setSelectedBarber(b)
        setFormData({ name: b.name || b.user_name || '', specialization: b.specialization || '', bio: b.bio || '', is_available: b.is_available ?? true })
        setIsEditModal(true)
    }

    const openScheduleModal = async (b) => {
        setSelectedBarber(b)
        try {
            const res = await apiFetch(`/barbers/${b.id}/schedule`)
            const data = await res.json()
            if (data.data?.schedule?.length) {
                setSchedule(data.data.schedule)
            } else {
                setSchedule(DAYS.map((_, i) => ({ day_of_week: i, is_working: i < 6, start_time: '09:00', end_time: '19:00' })))
            }
        } catch {
            setSchedule(DAYS.map((_, i) => ({ day_of_week: i, is_working: i < 6, start_time: '09:00', end_time: '19:00' })))
        }
        setIsScheduleModal(true)
    }

    const saveBarber = async (e) => {
        e.preventDefault()
        const res = await apiFetch(`/barbers/${selectedBarber.id}`, { method: 'PUT', body: JSON.stringify(formData) })
        if (res.ok) { setIsEditModal(false); load(); toast.success('Barbero actualizado correctamente') }
        else { const err = await res.json(); toast.error(err.detail || 'Error al guardar') }
    }

    const saveSchedule = async (e) => {
        e.preventDefault()
        const res = await apiFetch(`/barbers/${selectedBarber.id}/schedule`, { method: 'PUT', body: JSON.stringify({ schedule }) })
        if (res.ok) { setIsScheduleModal(false); toast.success('Horario guardado correctamente') }
        else { const err = await res.json(); toast.error(err.detail || 'Error al guardar horario') }
    }

    const updateDay = (idx, field, value) => {
        setSchedule(prev => prev.map((d, i) => i === idx ? { ...d, [field]: value } : d))
    }

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Equipo de <span className="text-gold">Barberos</span></h2>
                    <p className="ui-profile-subtitle">Gestión de maestros y horarios</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {barbers.map(b => (
                    <div key={b.id} className="ui-card-premium" style={{ padding: '1.5rem' }}>
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(212,175,55,0.1)', border: '2px solid rgba(212,175,55,0.3)', display: 'grid', placeItems: 'center', fontSize: '1.2rem', fontWeight: 900, color: 'var(--gold)' }}>
                                    {(b.name || b.user_name || 'B')[0].toUpperCase()}
                                </div>
                                <div>
                                    <p style={{ fontWeight: 900, fontSize: '14px' }}>{b.name || b.user_name || 'Barbero'}</p>
                                    <p style={{ fontSize: '10px', color: 'var(--gold)', textTransform: 'uppercase', fontWeight: 800 }}>{b.specialization || 'Especialista'}</p>
                                </div>
                            </div>
                            <span style={{ fontSize: '9px', fontWeight: 900, color: b.is_available ? '#4ade80' : '#f87171' }}>
                                {b.is_available ? '● Disponible' : '● No disponible'}
                            </span>
                        </div>

                        <div className="grid grid-cols-3 gap-2 mb-4">
                            <div style={{ textAlign: 'center', padding: '0.5rem', background: 'rgba(255,255,255,0.02)', borderRadius: '0.5rem' }}>
                                <p style={{ fontSize: '18px', fontWeight: 900 }}>{b.total_appointments || 0}</p>
                                <p style={{ fontSize: '8px', color: '#555', textTransform: 'uppercase' }}>Citas</p>
                            </div>
                            <div style={{ textAlign: 'center', padding: '0.5rem', background: 'rgba(255,255,255,0.02)', borderRadius: '0.5rem' }}>
                                <p style={{ fontSize: '18px', fontWeight: 900, color: 'var(--gold)' }}>{b.rating ? b.rating.toFixed(1) : '-'}</p>
                                <p style={{ fontSize: '8px', color: '#555', textTransform: 'uppercase' }}>Rating</p>
                            </div>
                            <div style={{ textAlign: 'center', padding: '0.5rem', background: 'rgba(255,255,255,0.02)', borderRadius: '0.5rem' }}>
                                <p style={{ fontSize: '18px', fontWeight: 900 }}>${b.total_earnings || 0}</p>
                                <p style={{ fontSize: '8px', color: '#555', textTransform: 'uppercase' }}>Ingresos</p>
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button onClick={() => openEditModal(b)} className="ui-btn" style={{ flex: 1, padding: '8px', background: 'rgba(255,255,255,0.03)', fontSize: '9px' }}>Editar Perfil</button>
                            <button onClick={() => openScheduleModal(b)} className="ui-btn-gold" style={{ flex: 1, padding: '8px', fontSize: '9px' }}>Horario</button>
                        </div>
                    </div>
                ))}
            </div>

            {loading && <p className="text-center py-12 text-muted animate-pulse">Cargando barberos...</p>}
            {!loading && barbers.length === 0 && <p className="text-center py-12" style={{ color: 'var(--muted)' }}>Sin barberos registrados.</p>}

            {/* Edit Modal */}
            <Modal isOpen={isEditModal} onClose={() => setIsEditModal(false)} title="Editar Perfil del Barbero"
                actions={<><button onClick={() => setIsEditModal(false)} className="ui-btn" style={{ background: 'transparent' }}>Cancelar</button><button onClick={saveBarber} className="ui-btn-gold">Guardar</button></>}>
                <form className="space-y-4">
                    <div className="group"><label className="ui-kpi-label">Nombre</label>
                        <input className="ui-input" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} placeholder="Nombre del barbero" /></div>
                    <div className="group"><label className="ui-kpi-label">Especialización</label>
                        <input className="ui-input" value={formData.specialization} onChange={e => setFormData({ ...formData, specialization: e.target.value })} placeholder="Ej: Cortes clásicos, barbas" /></div>
                    <div className="group"><label className="ui-kpi-label">Biografía</label>
                        <textarea className="ui-input" value={formData.bio} onChange={e => setFormData({ ...formData, bio: e.target.value })} placeholder="Descripción del barbero..." style={{ minHeight: '80px', resize: 'none' }} /></div>
                    <div className="group"><label className="ui-kpi-label">Disponibilidad</label>
                        <select className="ui-input" value={formData.is_available ? 'true' : 'false'} onChange={e => setFormData({ ...formData, is_available: e.target.value === 'true' })}>
                            <option value="true">Disponible</option><option value="false">No disponible</option></select></div>
                </form>
            </Modal>

            {/* Schedule Modal */}
            <Modal isOpen={isScheduleModal} onClose={() => setIsScheduleModal(false)} title={`Horario: ${selectedBarber?.name || selectedBarber?.user_name || ''}`}
                actions={<><button onClick={() => setIsScheduleModal(false)} className="ui-btn" style={{ background: 'transparent' }}>Cancelar</button><button onClick={saveSchedule} className="ui-btn-gold">Guardar Horario</button></>}>
                <div className="space-y-3">
                    {schedule.map((day, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.02)', borderRadius: '0.5rem' }}>
                            <div style={{ width: '90px' }}>
                                <p style={{ fontSize: '11px', fontWeight: 800, color: day.is_working ? '#fff' : '#444' }}>{DAYS[i]}</p>
                            </div>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                                <input type="checkbox" checked={day.is_working} onChange={e => updateDay(i, 'is_working', e.target.checked)} style={{ accentColor: 'var(--gold)', width: '14px', height: '14px' }} />
                                <span style={{ fontSize: '9px', fontWeight: 900, color: 'var(--muted)', textTransform: 'uppercase' }}>Trabaja</span>
                            </label>
                            {day.is_working && (
                                <>
                                    <input type="time" value={day.start_time} onChange={e => updateDay(i, 'start_time', e.target.value)} className="ui-input" style={{ width: '110px', padding: '6px 10px', fontSize: '12px' }} />
                                    <span style={{ color: '#444', fontSize: '12px' }}>—</span>
                                    <input type="time" value={day.end_time} onChange={e => updateDay(i, 'end_time', e.target.value)} className="ui-input" style={{ width: '110px', padding: '6px 10px', fontSize: '12px' }} />
                                </>
                            )}
                        </div>
                    ))}
                </div>
            </Modal>
        </div>
    )
}
