import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'
import Modal from '../../components/Modal'

const ROLES = [
    { value: 'admin', label: 'Administrador' },
    { value: 'barber', label: 'Barbero' },
    { value: 'client', label: 'Cliente' },
]

const ROLE_COLORS = { admin: '#d4af37', barber: '#60a5fa', client: '#4ade80' }

export default function AdminUsers() {
    const [users, setUsers] = useState([])
    const [loading, setLoading] = useState(true)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [editingUser, setEditingUser] = useState(null)

    const [formData, setFormData] = useState({
        name: '', email: '', password: '', role: 'client', phone: '', is_active: true
    })

    const load = async () => {
        setLoading(true)
        try {
            const res = await apiFetch('/users')
            const data = await res.json()
            setUsers(data.data?.users || data.data || [])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [])

    const openModal = (user = null) => {
        if (user) {
            setEditingUser(user)
            setFormData({ name: user.name || '', email: user.email || '', password: '', role: user.role || 'client', phone: user.phone || '', is_active: user.is_active ?? true })
        } else {
            setEditingUser(null)
            setFormData({ name: '', email: '', password: '', role: 'client', phone: '', is_active: true })
        }
        setIsModalOpen(true)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        const method = editingUser ? 'PUT' : 'POST'
        const url = editingUser ? `/users/${editingUser.id}` : '/users'
        const payload = { ...formData }
        if (editingUser && !payload.password) delete payload.password

        const res = await apiFetch(url, { method, body: JSON.stringify(payload) })
        if (res.ok) { setIsModalOpen(false); load(); toast.success('Usuario guardado correctamente') }
        else { const err = await res.json(); toast.error(err.detail || 'Error al guardar usuario') }
    }

    const toggleActive = async (user) => {
        await apiFetch(`/users/${user.id}`, { method: 'PUT', body: JSON.stringify({ ...user, is_active: !user.is_active }) })
        load()
    }

    const deleteUser = async (id) => {
        if (!window.confirm('¿Eliminar usuario permanentemente?')) return
        await apiFetch(`/users/${id}`, { method: 'DELETE' })
        load()
    }

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Gestión de <span className="text-gold">Usuarios</span></h2>
                    <p className="ui-profile-subtitle">Control de accesos y roles del sistema</p>
                </div>
                <button onClick={() => openModal()} className="ui-btn-gold">+ Nuevo Usuario</button>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {ROLES.map(r => (
                    <div key={r.value} className="ui-kpi-card">
                        <p className="ui-kpi-label">{r.label}s</p>
                        <p className="ui-kpi-value" style={{ color: ROLE_COLORS[r.value] }}>
                            {users.filter(u => u.role === r.value).length}
                        </p>
                    </div>
                ))}
            </div>

            <section className="ui-card-premium">
                <div className="ui-table-premium-wrapper">
                <table className="ui-table-premium">
                    <thead>
                        <tr style={{ background: 'transparent' }}>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Usuario</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Correo</th>
                            <th style={{ textAlign: 'center', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Rol</th>
                            <th style={{ textAlign: 'center', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Estado</th>
                            <th style={{ textAlign: 'right', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map((u, i) => (
                            <tr key={u.id ?? i}>
                                <td>
                                    <div style={{ fontWeight: 800 }}>{u.name}</div>
                                    <div style={{ fontSize: '10px', color: '#555' }}>{u.phone || 'Sin teléfono'}</div>
                                </td>
                                <td><span style={{ color: 'var(--muted)', fontSize: '13px' }}>{u.email}</span></td>
                                <td style={{ textAlign: 'center' }}>
                                    <span style={{ fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', color: ROLE_COLORS[u.role] || '#fff', background: `${ROLE_COLORS[u.role]}22`, padding: '3px 10px', borderRadius: '99px' }}>
                                        {ROLES.find(r => r.value === u.role)?.label || u.role}
                                    </span>
                                </td>
                                <td style={{ textAlign: 'center' }}>
                                    <button onClick={() => toggleActive(u)} style={{ fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', color: u.is_active !== false ? '#4ade80' : '#f87171', background: 'transparent', border: 'none', cursor: 'pointer' }}>
                                        {u.is_active !== false ? '● Activo' : '● Inactivo'}
                                    </button>
                                </td>
                                <td style={{ textAlign: 'right' }}>
                                    <button onClick={() => openModal(u)} className="ui-btn" style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.03)', marginRight: '8px' }}>Editar</button>
                                    <button onClick={() => deleteUser(u.id)} className="ui-btn" style={{ padding: '6px 12px', color: '#f87171' }}>Eliminar</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {loading && <p className="text-center py-12 text-muted animate-pulse">Cargando usuarios...</p>}
                {!loading && users.length === 0 && <p className="text-center py-12" style={{ color: 'var(--muted)' }}>Sin usuarios registrados.</p>}
                </div>
            </section>

            <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}
                actions={<><button onClick={() => setIsModalOpen(false)} className="ui-btn" style={{ background: 'transparent' }}>Cancelar</button><button onClick={handleSubmit} className="ui-btn-gold">Guardar</button></>}>
                <form className="space-y-4">
                    <div className="group"><label className="ui-kpi-label">Nombre Completo</label>
                        <input className="ui-input" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} placeholder="Nombre del usuario" required /></div>
                    <div className="group"><label className="ui-kpi-label">Correo Electrónico</label>
                        <input type="email" className="ui-input" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} placeholder="correo@example.com" disabled={!!editingUser} required /></div>
                    <div className="group"><label className="ui-kpi-label">{editingUser ? 'Nueva Contraseña (vacío = sin cambio)' : 'Contraseña'}</label>
                        <input type="password" className="ui-input" value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} placeholder="••••••••" required={!editingUser} /></div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="group"><label className="ui-kpi-label">Teléfono</label>
                            <input className="ui-input" value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} placeholder="+52 000 000 0000" /></div>
                        <div className="group"><label className="ui-kpi-label">Rol</label>
                            <select className="ui-input" value={formData.role} onChange={e => setFormData({ ...formData, role: e.target.value })}>
                                {ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}</select></div>
                    </div>
                    <div className="group"><label className="ui-kpi-label">Estado</label>
                        <select className="ui-input" value={formData.is_active ? 'true' : 'false'} onChange={e => setFormData({ ...formData, is_active: e.target.value === 'true' })}>
                            <option value="true">Activo</option><option value="false">Inactivo</option></select></div>
                </form>
            </Modal>
        </div>
    )
}
