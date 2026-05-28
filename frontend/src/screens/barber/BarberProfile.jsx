import { useEffect, useState } from 'react'
import { apiFetch, getStoredUser } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'

export default function BarberProfile() {
    const storedUser = getStoredUser()
    const [profile, setProfile] = useState(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [saved, setSaved] = useState(false)
    const [tab, setTab] = useState('profile')

    const [form, setForm] = useState({ name: '', email: '', phone: '', bio: '', specialization: '', avatar: '' })
    const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' })

    const load = async () => {
        setLoading(true)
        try {
            const res = await apiFetch('/profile')
            const data = await res.json()
            const p = data.data || data
            setProfile(p)
            setForm({ name: p.name || '', email: p.email || '', phone: p.phone || '', bio: p.bio || p.barber?.bio || '', specialization: p.barber?.specialization || '', avatar: p.avatar || p.barber?.avatar || '' })
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
            if (res.ok) {
                setSaved(true)
                setTimeout(() => setSaved(false), 3000)
                toast.success('Perfil guardado correctamente')
                load()
            } else {
                const err = await res.json()
                toast.error(err.detail || 'Error al guardar perfil')
            }
        } finally {
            setSaving(false)
        }
    }

    const changePassword = async (e) => {
        e.preventDefault()
        if (pwForm.new_password !== pwForm.confirm_password) return toast.warning('Las contraseñas no coinciden')
        if (pwForm.new_password.length < 6) return toast.warning('La contraseña debe tener al menos 6 caracteres')
        const res = await apiFetch('/profile/password', { method: 'PUT', body: JSON.stringify({ current_password: pwForm.current_password, new_password: pwForm.new_password }) })
        if (res.ok) { setPwForm({ current_password: '', new_password: '', confirm_password: '' }); toast.success('Contraseña actualizada correctamente') }
        else { const err = await res.json(); toast.error(err.detail || 'Error al cambiar contraseña') }
    }

    if (loading) return <div className="text-center py-20 text-muted animate-pulse">Cargando perfil...</div>

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Mi <span className="text-gold">Perfil</span></h2>
                    <p className="ui-profile-subtitle">Información personal y configuración</p>
                </div>
                {saved && <span style={{ fontSize: '10px', fontWeight: 900, color: '#4ade80', textTransform: 'uppercase' }}>✓ Guardado</span>}
            </div>

            {/* Avatar Card */}
            <section className="ui-card-premium" style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
                <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'rgba(212,175,55,0.1)', border: '3px solid rgba(212,175,55,0.3)', display: 'grid', placeItems: 'center', flexShrink: 0, overflow: 'hidden' }}>
                    {form.avatar ? (
                        <img src={form.avatar} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : (
                        <span style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--gold)' }}>{(form.name || 'B')[0].toUpperCase()}</span>
                    )}
                </div>
                <div>
                    <p style={{ fontWeight: 900, fontSize: '18px' }}>{form.name || 'Barbero'}</p>
                    <p style={{ fontSize: '11px', color: 'var(--gold)', fontWeight: 800, textTransform: 'uppercase' }}>{form.specialization || 'Barbero Profesional'}</p>
                    <p style={{ fontSize: '11px', color: 'var(--muted)' }}>{form.email}</p>
                </div>
            </section>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--line)', paddingBottom: '0' }}>
                {['profile', 'password'].map(t => (
                    <button key={t} onClick={() => setTab(t)} style={{ padding: '0.75rem 1.5rem', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', background: 'transparent', border: 'none', cursor: 'pointer', color: tab === t ? 'var(--gold)' : 'var(--muted)', borderBottom: tab === t ? '2px solid var(--gold)' : '2px solid transparent', marginBottom: '-1px' }}>
                        {t === 'profile' ? 'Perfil' : 'Contraseña'}
                    </button>
                ))}
            </div>

            {tab === 'profile' && (
                <form onSubmit={saveProfile} className="space-y-4">
                    <section className="ui-card-premium">
                        <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem', color: 'var(--gold)' }}>Datos Personales</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="group"><label className="ui-kpi-label">Nombre Completo</label>
                                <input className="ui-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Tu nombre" /></div>
                            <div className="group"><label className="ui-kpi-label">Teléfono</label>
                                <input className="ui-input" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="+52 000 000 0000" /></div>
                            <div className="group"><label className="ui-kpi-label">Especialización</label>
                                <input className="ui-input" value={form.specialization} onChange={e => setForm({ ...form, specialization: e.target.value })} placeholder="Ej: Cortes clásicos, barbas" /></div>
                            <div className="group"><label className="ui-kpi-label">URL Avatar (foto)</label>
                                <input className="ui-input" value={form.avatar} onChange={e => setForm({ ...form, avatar: e.target.value })} placeholder="https://..." /></div>
                            <div className="group md:col-span-2"><label className="ui-kpi-label">Biografía</label>
                                <textarea className="ui-input" value={form.bio} onChange={e => setForm({ ...form, bio: e.target.value })} placeholder="Cuéntanos sobre ti y tu experiencia..." style={{ minHeight: '100px', resize: 'none' }} /></div>
                        </div>
                    </section>
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <button type="submit" disabled={saving} className="ui-btn-gold" style={{ opacity: saving ? 0.6 : 1 }}>
                            {saving ? 'Guardando...' : 'Guardar Perfil'}
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
                            <div className="group"><label className="ui-kpi-label">Confirmar Nueva Contraseña</label>
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
