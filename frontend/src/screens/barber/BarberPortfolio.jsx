import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'
import Modal from '../../components/Modal'

export default function BarberPortfolio() {
    const [works, setWorks] = useState([])
    const [loading, setLoading] = useState(true)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [selectedWork, setSelectedWork] = useState(null)

    const [formData, setFormData] = useState({
        title: '',
        description: '',
        service_type: 'haircut',
        before_image_url: '',
        after_image_url: '',
    })

    const load = async () => {
        setLoading(true)
        try {
            const res = await apiFetch('/barber/portfolio')
            const data = await res.json()
            setWorks(Array.isArray(data) ? data : (data.data?.works || data.data || []))
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [])

    const openModal = (work = null) => {
        if (work) {
            setSelectedWork(work)
            setFormData({ title: work.title || '', description: work.description || '', service_type: work.service_type || 'haircut', before_image_url: work.before_image_url || '', after_image_url: work.after_image_url || '' })
        } else {
            setSelectedWork(null)
            setFormData({ title: '', description: '', service_type: 'haircut', before_image_url: '', after_image_url: '' })
        }
        setIsModalOpen(true)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        const method = selectedWork ? 'PUT' : 'POST'
        const url = selectedWork ? `/barber/portfolio/${selectedWork.id}` : '/barber/portfolio'
        const res = await apiFetch(url, { method, body: JSON.stringify(formData) })
        if (res.ok) { setIsModalOpen(false); load(); toast.success('Trabajo guardado en el portafolio') }
        else { const err = await res.json(); toast.error(err.detail || 'Error al guardar trabajo') }
    }

    const deleteWork = async (id) => {
        if (!window.confirm('¿Eliminar este trabajo del portafolio?')) return
        await apiFetch(`/barber/portfolio/${id}`, { method: 'DELETE' })
        load()
    }

    const SERVICE_LABELS = { haircut: 'Corte', shaving: 'Barba', coloring: 'Color', styling: 'Styling', treatment: 'Tratamiento', combo: 'Combo' }

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Mi <span className="text-gold">Portafolio</span></h2>
                    <p className="ui-profile-subtitle">Galería de trabajos y creaciones</p>
                </div>
                <button onClick={() => openModal()} className="ui-btn-gold">+ Agregar Trabajo</button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Trabajos</p>
                    <p className="ui-kpi-value">{works.length}</p>
                </div>
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Me Gusta</p>
                    <p className="ui-kpi-value" style={{ color: 'var(--gold)' }}>
                        {works.reduce((s, w) => s + (w.reactions_count || w.likes || 0), 0)}
                    </p>
                </div>
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Comentarios</p>
                    <p className="ui-kpi-value">{works.reduce((s, w) => s + (w.comments_count || w.comments || 0), 0)}</p>
                </div>
            </div>

            {/* Works Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {works.map(w => (
                    <div key={w.id} className="ui-card-premium" style={{ padding: '0', overflow: 'hidden' }}>
                        {/* Before/After Images */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', height: '160px', gap: '1px', background: 'var(--line)' }}>
                            <div style={{ background: '#0f0f0f', display: 'grid', placeItems: 'center', position: 'relative' }}>
                                {w.before_image_url ? (
                                    <img src={w.before_image_url} alt="Antes" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                ) : (
                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: '24px' }}>📷</div>
                                        <p style={{ fontSize: '8px', color: '#333', marginTop: '4px' }}>ANTES</p>
                                    </div>
                                )}
                                <div style={{ position: 'absolute', bottom: '4px', left: '4px', background: 'rgba(0,0,0,0.7)', padding: '2px 6px', borderRadius: '3px', fontSize: '7px', fontWeight: 900, color: '#888' }}>ANTES</div>
                            </div>
                            <div style={{ background: '#0f0f0f', display: 'grid', placeItems: 'center', position: 'relative' }}>
                                {w.after_image_url ? (
                                    <img src={w.after_image_url} alt="Después" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                ) : (
                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: '24px' }}>📷</div>
                                        <p style={{ fontSize: '8px', color: '#333', marginTop: '4px' }}>DESPUÉS</p>
                                    </div>
                                )}
                                <div style={{ position: 'absolute', bottom: '4px', right: '4px', background: 'rgba(212,175,55,0.8)', padding: '2px 6px', borderRadius: '3px', fontSize: '7px', fontWeight: 900, color: '#000' }}>DESPUÉS</div>
                            </div>
                        </div>

                        <div style={{ padding: '1.25rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                                <div>
                                    <p style={{ fontWeight: 900, fontSize: '14px' }}>{w.title || 'Sin título'}</p>
                                    <span style={{ fontSize: '9px', fontWeight: 900, color: 'var(--gold)', textTransform: 'uppercase' }}>{SERVICE_LABELS[w.service_type] || w.service_type}</span>
                                </div>
                                <div style={{ display: 'flex', gap: '0.75rem', fontSize: '10px', color: '#555' }}>
                                    <span>♥ {w.reactions_count || w.likes || 0}</span>
                                    <span>💬 {w.comments_count || w.comments || 0}</span>
                                </div>
                            </div>
                            {w.description && <p style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '1rem', lineHeight: 1.5 }}>{w.description}</p>}
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <button onClick={() => openModal(w)} className="ui-btn" style={{ flex: 1, padding: '6px', background: 'rgba(255,255,255,0.03)', fontSize: '9px' }}>Editar</button>
                                <button onClick={() => deleteWork(w.id)} className="ui-btn" style={{ padding: '6px 10px', color: '#f87171', fontSize: '9px' }}>✕</button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {loading && <p className="text-center py-12 text-muted animate-pulse">Cargando portafolio...</p>}
            {!loading && works.length === 0 && (
                <div className="text-center" style={{ padding: '4rem', color: 'var(--muted)' }}>
                    <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📸</div>
                    <p style={{ fontWeight: 800 }}>Aún no tienes trabajos en tu portafolio</p>
                    <p style={{ fontSize: '12px', marginTop: '0.5rem' }}>Agrega tu primer antes/después para mostrar tu talento</p>
                </div>
            )}

            <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={selectedWork ? 'Editar Trabajo' : 'Nuevo Trabajo'}
                actions={<><button onClick={() => setIsModalOpen(false)} className="ui-btn" style={{ background: 'transparent' }}>Cancelar</button><button onClick={handleSubmit} className="ui-btn-gold">Guardar</button></>}>
                <form className="space-y-4">
                    <div className="group"><label className="ui-kpi-label">Título del Trabajo</label>
                        <input className="ui-input" value={formData.title} onChange={e => setFormData({ ...formData, title: e.target.value })} placeholder="Ej: Corte degradé clásico" required /></div>
                    <div className="group"><label className="ui-kpi-label">Tipo de Servicio</label>
                        <select className="ui-input" value={formData.service_type} onChange={e => setFormData({ ...formData, service_type: e.target.value })}>
                            {Object.entries(SERVICE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></div>
                    <div className="group"><label className="ui-kpi-label">Descripción (opcional)</label>
                        <textarea className="ui-input" value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })} placeholder="Describe el trabajo realizado..." style={{ minHeight: '60px', resize: 'none' }} /></div>
                    <div className="group"><label className="ui-kpi-label">URL Foto Antes</label>
                        <input className="ui-input" value={formData.before_image_url} onChange={e => setFormData({ ...formData, before_image_url: e.target.value })} placeholder="https://..." /></div>
                    <div className="group"><label className="ui-kpi-label">URL Foto Después</label>
                        <input className="ui-input" value={formData.after_image_url} onChange={e => setFormData({ ...formData, after_image_url: e.target.value })} placeholder="https://..." /></div>
                </form>
            </Modal>
        </div>
    )
}
