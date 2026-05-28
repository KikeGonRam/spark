import { useState, useEffect } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'
import Modal from '../../components/Modal'

export default function AdminServices() {
    const [services, setServices] = useState([])
    const [loading, setLoading] = useState(true)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [editingService, setEditingService] = useState(null)
    
    // Sincronizado con ServiceCreate (FastAPI)
    const [formData, setFormData] = useState({ 
        name: '', 
        description: '', 
        price: '', 
        duration_minutes: 30, 
        category: 'haircut',
        is_active: true
    })

    const load = async () => {
        setLoading(true)
        try {
            const res = await apiFetch('/services')
            const data = await res.json()
            setServices(data.data?.services || [])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [])

    const handleOpenModal = (service = null) => {
        if (service) {
            setEditingService(service)
            setFormData({
                name: service.name || '',
                description: service.description || '',
                price: service.price || '',
                duration_minutes: service.duration || 30,
                category: service.category || 'haircut',
                is_active: service.is_active ?? true
            })
        } else {
            setEditingService(null)
            setFormData({ name: '', description: '', price: '', duration_minutes: 30, category: 'haircut', is_active: true })
        }
        setIsModalOpen(true)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        const method = editingService ? 'PUT' : 'POST'
        const url = editingService ? `/services/${editingService.id}` : '/services'
        
        // Convertimos price a float y duration a int para el backend
        const payload = {
            ...formData,
            price: parseFloat(formData.price),
            duration_minutes: parseInt(formData.duration_minutes)
        }

        try {
            const res = await apiFetch(url, {
                method,
                body: JSON.stringify(payload)
            })
            if (res.ok) {
                setIsModalOpen(false)
                load()
            } else {
                const err = await res.json()
                toast.error(err.detail || 'No se pudo guardar el servicio')
            }
        } catch (error) {
            console.error("Error saving service", error)
        }
    }

    const handleDelete = async (id) => {
        if (!window.confirm('¿Estás seguro de eliminar este servicio?')) return
        await apiFetch(`/services/${id}`, { method: 'DELETE' })
        load()
    }

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Gestión de <span className="text-gold">Servicios</span></h2>
                    <p className="ui-profile-subtitle">Catálogo de experiencias premium</p>
                </div>
                <button onClick={() => handleOpenModal()} className="ui-btn-gold">+ Nuevo Servicio</button>
            </div>

            <section className="ui-card-premium">
                <div className="ui-table-premium-wrapper">
                <table className="ui-table-premium">
                    <thead>
                        <tr style={{ background: 'transparent' }}>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Servicio</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Precio</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Duración</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Estado</th>
                            <th style={{ textAlign: 'right', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {services.map((s, i) => (
                            <tr key={s.id ?? i}>
                                <td>
                                    <div style={{ fontWeight: 800 }}>{s.name}</div>
                                    <div style={{ fontSize: '11px', color: '#555' }}>{s.category}</div>
                                </td>
                                <td><span className="text-gold font-bold">${s.price}</span></td>
                                <td><span style={{ color: 'var(--muted)', fontSize: '12px' }}>{s.duration} min</span></td>
                                <td>
                                    <span style={{ fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', color: s.is_active ? '#4ade80' : '#f87171' }}>
                                        {s.is_active ? 'Activo' : 'Inactivo'}
                                    </span>
                                </td>
                                <td style={{ textAlign: 'right' }}>
                                    <button onClick={() => handleOpenModal(s)} className="ui-btn" style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.03)', marginRight: '8px' }}>Editar</button>
                                    <button onClick={() => handleDelete(s.id)} className="ui-btn" style={{ padding: '6px 12px', color: '#f87171' }}>Borrar</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {loading && <p className="text-center py-12 text-muted animate-pulse">Sincronizando servicios...</p>}
                </div>
            </section>

            <Modal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)}
                title={editingService ? 'Editar Servicio' : 'Nuevo Servicio'}
                actions={
                    <>
                        <button onClick={() => setIsModalOpen(false)} className="ui-btn" style={{ background: 'transparent' }}>Cancelar</button>
                        <button onClick={handleSubmit} className="ui-btn-gold">Guardar Cambios</button>
                    </>
                }
            >
                <form className="space-y-4">
                    <div className="group">
                        <label className="ui-kpi-label">Nombre del Servicio</label>
                        <input 
                            className="ui-input" 
                            value={formData.name} 
                            onChange={e => setFormData({...formData, name: e.target.value})}
                            placeholder="Ej: Corte Signature"
                            required
                        />
                    </div>
                    <div className="group">
                        <label className="ui-kpi-label">Descripción</label>
                        <textarea 
                            className="ui-input" 
                            value={formData.description} 
                            onChange={e => setFormData({...formData, description: e.target.value})}
                            placeholder="Breve descripción de la experiencia..."
                            style={{ minHeight: '80px', resize: 'none' }}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="group">
                            <label className="ui-kpi-label">Precio ($)</label>
                            <input 
                                type="number" step="0.01"
                                className="ui-input" 
                                value={formData.price} 
                                onChange={e => setFormData({...formData, price: e.target.value})}
                                placeholder="350"
                                required
                            />
                        </div>
                        <div className="group">
                            <label className="ui-kpi-label">Duración (min)</label>
                            <input 
                                type="number"
                                className="ui-input" 
                                value={formData.duration_minutes} 
                                onChange={e => setFormData({...formData, duration_minutes: e.target.value})}
                                placeholder="30"
                                required
                            />
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="group">
                            <label className="ui-kpi-label">Categoría</label>
                            <select 
                                className="ui-input" 
                                value={formData.category}
                                onChange={e => setFormData({...formData, category: e.target.value})}
                            >
                                <option value="haircut">Corte de Cabello</option>
                                <option value="shaving">Barba & Ritual</option>
                                <option value="treatment">Tratamientos</option>
                                <option value="coloring">Coloración</option>
                                <option value="styling">Styling</option>
                                <option value="combo">Combos</option>
                            </select>
                        </div>
                        <div className="group">
                            <label className="ui-kpi-label">Estado</label>
                            <select 
                                className="ui-input" 
                                value={formData.is_active ? "true" : "false"}
                                onChange={e => setFormData({...formData, is_active: e.target.value === "true"})}
                            >
                                <option value="true">Activo</option>
                                <option value="false">Inactivo</option>
                            </select>
                        </div>
                    </div>
                </form>
            </Modal>
        </div>
    )
}
