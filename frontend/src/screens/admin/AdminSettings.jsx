import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'

export default function AdminSettings() {
    const [settings, setSettings] = useState(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [saved, setSaved] = useState(false)

    const [form, setForm] = useState({
        shop_name: '',
        shop_address: '',
        shop_phone: '',
        shop_email: '',
        shop_description: '',
        cancellation_policy_hours: 24,
        instagram: '',
        facebook: '',
        whatsapp: '',
        maintenance_mode: false,
        booking_advance_days: 30,
        slot_duration_minutes: 30,
    })

    const load = async () => {
        setLoading(true)
        try {
            const res = await apiFetch('/settings')
            const data = await res.json()
            const s = data.data || data
            setSettings(s)
            setForm({
                shop_name: s.shop_name || s.name || '',
                shop_address: s.shop_address || s.address || '',
                shop_phone: s.shop_phone || s.phone || '',
                shop_email: s.shop_email || s.email || '',
                shop_description: s.shop_description || s.description || '',
                cancellation_policy_hours: s.cancellation_policy_hours ?? 24,
                instagram: s.instagram || '',
                facebook: s.facebook || '',
                whatsapp: s.whatsapp || '',
                maintenance_mode: s.maintenance_mode ?? false,
                booking_advance_days: s.booking_advance_days ?? 30,
                slot_duration_minutes: s.slot_duration_minutes ?? 30,
            })
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [])

    const handleSave = async (e) => {
        e.preventDefault()
        setSaving(true)
        try {
            const res = await apiFetch('/settings', { method: 'PUT', body: JSON.stringify(form) })
            if (res.ok) { setSaved(true); setTimeout(() => setSaved(false), 3000); toast.success('Configuración guardada') }
            else { const err = await res.json(); toast.error(err.detail || 'Error al guardar') }
        } finally {
            setSaving(false)
        }
    }

    const toggleMaintenance = async () => {
        const newVal = !form.maintenance_mode
        setForm(f => ({ ...f, maintenance_mode: newVal }))
        await apiFetch('/settings/maintenance', { method: 'POST', body: JSON.stringify({ enabled: newVal }) })
    }

    if (loading) return <div className="text-center py-20 text-muted animate-pulse">Cargando configuración...</div>

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Configuración <span className="text-gold">General</span></h2>
                    <p className="ui-profile-subtitle">Ajustes globales de la barbería</p>
                </div>
                {saved && (
                    <span style={{ fontSize: '10px', fontWeight: 900, color: '#4ade80', textTransform: 'uppercase', letterSpacing: '0.1em' }}>✓ Guardado</span>
                )}
            </div>

            <form onSubmit={handleSave} className="space-y-6">
                {/* Información General */}
                <section className="ui-card-premium">
                    <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem', color: 'var(--gold)' }}>Información del Negocio</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="group"><label className="ui-kpi-label">Nombre de la Barbería</label>
                            <input className="ui-input" value={form.shop_name} onChange={e => setForm({ ...form, shop_name: e.target.value })} placeholder="BarberPro" /></div>
                        <div className="group"><label className="ui-kpi-label">Teléfono</label>
                            <input className="ui-input" value={form.shop_phone} onChange={e => setForm({ ...form, shop_phone: e.target.value })} placeholder="+52 000 000 0000" /></div>
                        <div className="group md:col-span-2"><label className="ui-kpi-label">Dirección</label>
                            <input className="ui-input" value={form.shop_address} onChange={e => setForm({ ...form, shop_address: e.target.value })} placeholder="Calle, Ciudad, Estado" /></div>
                        <div className="group"><label className="ui-kpi-label">Correo Electrónico</label>
                            <input type="email" className="ui-input" value={form.shop_email} onChange={e => setForm({ ...form, shop_email: e.target.value })} placeholder="contacto@barberpro.mx" /></div>
                        <div className="group md:col-span-2"><label className="ui-kpi-label">Descripción</label>
                            <textarea className="ui-input" value={form.shop_description} onChange={e => setForm({ ...form, shop_description: e.target.value })} placeholder="Descripción corta del negocio..." style={{ minHeight: '80px', resize: 'none' }} /></div>
                    </div>
                </section>

                {/* Redes Sociales */}
                <section className="ui-card-premium">
                    <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem', color: 'var(--gold)' }}>Redes Sociales</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="group"><label className="ui-kpi-label">Instagram</label>
                            <input className="ui-input" value={form.instagram} onChange={e => setForm({ ...form, instagram: e.target.value })} placeholder="@barberpro" /></div>
                        <div className="group"><label className="ui-kpi-label">Facebook</label>
                            <input className="ui-input" value={form.facebook} onChange={e => setForm({ ...form, facebook: e.target.value })} placeholder="BarberPro" /></div>
                        <div className="group"><label className="ui-kpi-label">WhatsApp</label>
                            <input className="ui-input" value={form.whatsapp} onChange={e => setForm({ ...form, whatsapp: e.target.value })} placeholder="+52 000 000 0000" /></div>
                    </div>
                </section>

                {/* Reservaciones */}
                <section className="ui-card-premium">
                    <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem', color: 'var(--gold)' }}>Política de Reservaciones</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="group"><label className="ui-kpi-label">Política de Cancelación (horas)</label>
                            <input type="number" min="0" className="ui-input" value={form.cancellation_policy_hours} onChange={e => setForm({ ...form, cancellation_policy_hours: parseInt(e.target.value) })} /></div>
                        <div className="group"><label className="ui-kpi-label">Reservar hasta (días anticipación)</label>
                            <input type="number" min="1" className="ui-input" value={form.booking_advance_days} onChange={e => setForm({ ...form, booking_advance_days: parseInt(e.target.value) })} /></div>
                        <div className="group"><label className="ui-kpi-label">Duración de Slot (minutos)</label>
                            <select className="ui-input" value={form.slot_duration_minutes} onChange={e => setForm({ ...form, slot_duration_minutes: parseInt(e.target.value) })}>
                                <option value={15}>15 minutos</option>
                                <option value={30}>30 minutos</option>
                                <option value={60}>60 minutos</option>
                            </select></div>
                    </div>
                </section>

                {/* Modo Mantenimiento */}
                <section className="ui-card-premium">
                    <div className="flex justify-between items-center">
                        <div>
                            <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', color: form.maintenance_mode ? '#f87171' : 'var(--gold)' }}>
                                Modo Mantenimiento
                            </h3>
                            <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '4px' }}>
                                {form.maintenance_mode ? 'El sistema está en mantenimiento. Los clientes no pueden acceder.' : 'El sistema está operativo y disponible.'}
                            </p>
                        </div>
                        <button type="button" onClick={toggleMaintenance} style={{ padding: '10px 20px', borderRadius: '0.75rem', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', border: 'none', cursor: 'pointer', background: form.maintenance_mode ? 'rgba(239,68,68,0.15)' : 'rgba(74,222,128,0.1)', color: form.maintenance_mode ? '#f87171' : '#4ade80' }}>
                            {form.maintenance_mode ? 'Desactivar' : 'Activar'}
                        </button>
                    </div>
                </section>

                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <button type="submit" disabled={saving} className="ui-btn-gold" style={{ opacity: saving ? 0.6 : 1 }}>
                        {saving ? 'Guardando...' : 'Guardar Configuración'}
                    </button>
                </div>
            </form>
        </div>
    )
}
