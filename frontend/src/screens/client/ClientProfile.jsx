import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'

const TIER_COLORS = { bronze: '#cd7f32', silver: '#c0c0c0', gold: '#d4af37', platinum: '#e5e4e2' }
const TIER_LABELS = { bronze: 'Bronce', silver: 'Plata', gold: 'Oro', platinum: 'Platino' }

export default function ClientProfile() {
    const [profile, setProfile] = useState(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [saved, setSaved] = useState(false)
    const [tab, setTab] = useState('profile')

    const [form, setForm] = useState({ name: '', phone: '', address: '', city: '' })
    const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' })

    const load = async () => {
        setLoading(true)
        try {
            const res = await apiFetch('/profile')
            const data = await res.json()
            const p = data.data || data
            setProfile(p)
            setForm({ name: p.name || '', phone: p.phone || p.client?.phone || '', address: p.client?.address || '', city: p.client?.city || '' })
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [])

    const saveProfile = async (e) => {
        e.preventDefault()
        setSaving(true)
        try {
            const res = await apiFetch('/profile', { method: 'PUT', body: JSON.stringify(form) })
            if (res.ok) { setSaved(true); setTimeout(() => setSaved(false), 3000); load(); toast.success('Perfil actualizado correctamente') }
            else { const err = await res.json(); toast.error(err.detail || 'Error al guardar') }
        } finally {
            setSaving(false)
        }
    }

    const changePassword = async (e) => {
        e.preventDefault()
        if (pwForm.new_password !== pwForm.confirm_password) return toast.warning('Las contraseñas no coinciden')
        const res = await apiFetch('/profile/password', { method: 'PUT', body: JSON.stringify({ current_password: pwForm.current_password, new_password: pwForm.new_password }) })
        if (res.ok) { setPwForm({ current_password: '', new_password: '', confirm_password: '' }); toast.success('Contraseña actualizada correctamente') }
        else { const err = await res.json(); toast.error(err.detail || 'Error al cambiar contraseña') }
    }

    if (loading) return <div className="text-center py-20 text-muted animate-pulse">Cargando perfil...</div>

    const client = profile?.client || {}
    const tier = client.loyalty_tier || 'bronze'
    const points = client.loyalty_points || 0
    const totalSpent = client.total_spent || 0
    const completedApps = client.completed_appointments || 0

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Mi <span className="text-gold">Perfil</span></h2>
                    <p className="ui-profile-subtitle">Cuenta premium y beneficios exclusivos</p>
                </div>
                {saved && <span style={{ fontSize: '10px', fontWeight: 900, color: '#4ade80', textTransform: 'uppercase' }}>✓ Guardado</span>}
            </div>

            {/* Loyalty Card */}
            <div style={{ background: `linear-gradient(135deg, ${TIER_COLORS[tier]}22, rgba(0,0,0,0))`, border: `1px solid ${TIER_COLORS[tier]}44`, borderRadius: '1.25rem', padding: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem' }}>
                <div>
                    <p style={{ fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.18em', color: TIER_COLORS[tier], marginBottom: '6px' }}>Membresía {TIER_LABELS[tier]}</p>
                    <p style={{ fontSize: '2.5rem', fontWeight: 900, color: '#fff', lineHeight: 1 }}>{form.name || 'Cliente'}</p>
                    <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '6px' }}>{profile?.email}</p>
                </div>
                <div style={{ display: 'flex', gap: '2rem' }}>
                    <div style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: '2rem', fontWeight: 900, color: TIER_COLORS[tier] }}>{points}</p>
                        <p style={{ fontSize: '8px', fontWeight: 900, textTransform: 'uppercase', color: '#555' }}>Puntos</p>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: '2rem', fontWeight: 900 }}>{completedApps}</p>
                        <p style={{ fontSize: '8px', fontWeight: 900, textTransform: 'uppercase', color: '#555' }}>Visitas</p>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: '2rem', fontWeight: 900, color: '#4ade80' }}>${totalSpent}</p>
                        <p style={{ fontSize: '8px', fontWeight: 900, textTransform: 'uppercase', color: '#555' }}>Total</p>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--line)' }}>
                {['profile', 'password'].map(t => (
                    <button key={t} onClick={() => setTab(t)} style={{ padding: '0.75rem 1.5rem', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', background: 'transparent', border: 'none', cursor: 'pointer', color: tab === t ? 'var(--gold)' : 'var(--muted)', borderBottom: tab === t ? '2px solid var(--gold)' : '2px solid transparent', marginBottom: '-1px' }}>
                        {t === 'profile' ? 'Mis Datos' : 'Contraseña'}
                    </button>
                ))}
            </div>

            {tab === 'profile' && (
                <form onSubmit={saveProfile} className="space-y-4">
                    <section className="ui-card-premium">
                        <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem', color: 'var(--gold)' }}>Información Personal</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="group"><label className="ui-kpi-label">Nombre Completo</label>
                                <input className="ui-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Tu nombre completo" /></div>
                            <div className="group"><label className="ui-kpi-label">Teléfono</label>
                                <input className="ui-input" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="+52 000 000 0000" /></div>
                            <div className="group"><label className="ui-kpi-label">Dirección</label>
                                <input className="ui-input" value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} placeholder="Calle y número" /></div>
                            <div className="group"><label className="ui-kpi-label">Ciudad</label>
                                <input className="ui-input" value={form.city} onChange={e => setForm({ ...form, city: e.target.value })} placeholder="Tu ciudad" /></div>
                        </div>
                    </section>
                    {client.referral_code && (
                        <section className="ui-card-premium">
                            <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1rem', color: 'var(--gold)' }}>Código de Referido</h3>
                            <div style={{ background: 'rgba(212,175,55,0.06)', border: '1px dashed rgba(212,175,55,0.3)', borderRadius: '0.75rem', padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <code style={{ fontFamily: 'monospace', fontSize: '18px', fontWeight: 900, color: 'var(--gold)', letterSpacing: '0.2em' }}>{client.referral_code}</code>
                                <button type="button" onClick={() => navigator.clipboard?.writeText(client.referral_code)} className="ui-btn" style={{ padding: '6px 12px', background: 'transparent', border: '1px solid var(--line)', fontSize: '9px' }}>Copiar</button>
                            </div>
                            <p style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '0.5rem' }}>Comparte tu código y gana puntos por cada referido que haga su primera cita.</p>
                        </section>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <button type="submit" disabled={saving} className="ui-btn-gold" style={{ opacity: saving ? 0.6 : 1 }}>
                            {saving ? 'Guardando...' : 'Guardar Cambios'}
                        </button>
                    </div>
                </form>
            )}

            {tab === 'password' && (
                <form onSubmit={changePassword} className="space-y-4">
                    <section className="ui-card-premium">
                        <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem', color: 'var(--gold)' }}>Cambiar Contraseña</h3>
                        <div className="space-y-4" style={{ maxWidth: '400px' }}>
                            <div className="group"><label className="ui-kpi-label">Contraseña Actual</label>
                                <input type="password" className="ui-input" value={pwForm.current_password} onChange={e => setPwForm({ ...pwForm, current_password: e.target.value })} placeholder="••••••••" required /></div>
                            <div className="group"><label className="ui-kpi-label">Nueva Contraseña</label>
                                <input type="password" className="ui-input" value={pwForm.new_password} onChange={e => setPwForm({ ...pwForm, new_password: e.target.value })} placeholder="••••••••" required /></div>
                            <div className="group"><label className="ui-kpi-label">Confirmar Contraseña</label>
                                <input type="password" className="ui-input" value={pwForm.confirm_password} onChange={e => setPwForm({ ...pwForm, confirm_password: e.target.value })} placeholder="••••••••" required /></div>
                        </div>
                    </section>
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <button type="submit" className="ui-btn-gold">Cambiar Contraseña</button>
                    </div>
                </form>
            )}
        </div>
    )
}
