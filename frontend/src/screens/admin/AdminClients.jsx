import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'
import Modal from '../../components/Modal'

export default function AdminClients() {
    const [clients, setClients] = useState([])
    const [loading, setLoading] = useState(true)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [editingClient, setEditingClient] = useState(null)
    
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        password: '',
        address: '',
        city: '',
        is_vip: false
    })

    const load = async () => {
        setLoading(true)
        try {
            const res = await apiFetch('/clients')
            const data = await res.json()
            setClients(data.data?.clients || [])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [])

    const handleOpenModal = (client = null) => {
        if (client) {
            setEditingClient(client)
            setFormData({
                first_name: client.first_name || '',
                last_name: client.last_name || '',
                email: client.email || '',
                phone: client.phone || '',
                address: client.address || '',
                city: client.city || '',
                is_vip: client.is_vip ?? false
            })
        } else {
            setEditingClient(null)
            setFormData({ first_name: '', last_name: '', email: '', phone: '', password: '', address: '', city: '', is_vip: false })
        }
        setIsModalOpen(true)
    }

    const [errors, setErrors] = useState({})
    const [showPassword, setShowPassword] = useState(false)
    const [passwordStrength, setPasswordStrength] = useState(0)

    const calcStrength = (pwd='') => {
        let score = 0
        if (pwd.length >= 8) score += 1
        if (/[A-Z]/.test(pwd)) score += 1
        if (/[0-9]/.test(pwd)) score += 1
        if (/[!@#\$%\^&\*(),.?:{}|<>]/.test(pwd)) score += 1
        setPasswordStrength(score)
        return score
    }

    const validateForm = () => {
        const err = {}
        if (!formData.first_name) err.first_name = 'Nombre es requerido'
        if (!formData.last_name) err.last_name = 'Apellido es requerido'
        if (!formData.email) err.email = 'Email es requerido'
        if (!editingClient) {
                    const pwd = formData.password || ''
                    const hasMin = pwd.length >= 8
                    const hasSpecial = /[!@#\$%\^&\*(),.?:{}|<>]/.test(pwd)
                    if (!hasMin) err.password = 'La contraseña debe tener al menos 8 caracteres'
                    else if (!hasSpecial) err.password = 'La contraseña debe contener al menos 1 carácter especial (ej. !@#$%)'
                }
        setErrors(err)
        return Object.keys(err).length === 0
    }

    const handleSubmit = async (e) => {
        e && e.preventDefault()

        if (!validateForm()) return

        e.preventDefault()

        try {
            if (editingClient) {
                // Solo actualiza datos del cliente (is_vip, address, city)
                const res = await apiFetch(`/clients/${editingClient.id}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ is_vip: formData.is_vip, address: formData.address, city: formData.city })
                })
                if (res.ok) { setIsModalOpen(false); load() }
                else { const err = await res.json(); toast.error(err.detail || 'No se pudo actualizar el cliente') }
            } else {
                // Paso 1: crear User con role=client
                const userRes = await apiFetch('/users', {
                    method: 'POST',
                    body: JSON.stringify({
                        name: `${formData.first_name} ${formData.last_name}`.trim(),
                        email: formData.email,
                        phone: formData.phone,
                        password: formData.password,
                        role: 'client'
                    })
                })
                if (!userRes.ok) {
                    const err = await userRes.json().catch(()=>({detail:'Error en la respuesta'}))
                    toast.error(err.detail || 'No se pudo crear el usuario')
                    return
                }
                const userData = await userRes.json()
                const userId = userData.data?.user?.id || userData.data?.user?._id

                // Paso 2: crear perfil Client vinculado al User
                const clientRes = await apiFetch('/clients', {
                    method: 'POST',
                    body: JSON.stringify({ user_id: userId, is_vip: formData.is_vip, address: formData.address, city: formData.city })
                })
                if (clientRes.ok) { setIsModalOpen(false); load(); toast.success('Cliente registrado correctamente') }
                else { const err = await clientRes.json().catch(()=>({detail:'Error en la respuesta'})); toast.error(err.detail || 'Usuario creado pero el perfil de cliente falló') }
            }
        } catch (error) {
            console.error("Error saving client", error)
            toast.error('Error de conexión')
        }
    }

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Directorio de <span className="text-gold">Clientes</span></h2>
                    <p className="ui-profile-subtitle">Gestión de la base de caballeros</p>
                </div>
                <button onClick={() => handleOpenModal()} className="ui-btn-gold">+ Nuevo Cliente</button>
            </div>

            <section className="ui-card-premium">
                <div className="ui-table-premium-wrapper">
                <table className="ui-table-premium">
                    <thead>
                        <tr style={{ background: 'transparent' }}>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Nombre Completo</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Email</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Teléfono</th>
                            <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Status</th>
                            <th style={{ textAlign: 'right', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {clients.map((c, i) => (
                            <tr key={c.id ?? i}>
                                <td>
                                    <div style={{ fontWeight: 800 }}>{c.first_name} {c.last_name}</div>
                                    <div style={{ fontSize: '10px', color: c.is_vip ? 'var(--gold)' : '#555', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                                        {c.is_vip ? 'Caballero VIP' : 'Cliente Estándar'}
                                    </div>
                                </td>
                                <td><span style={{ color: 'var(--muted)' }}>{c.email}</span></td>
                                <td><span style={{ color: 'var(--muted)' }}>{c.phone || '-'}</span></td>
                                <td><span style={{ fontSize: '10px', fontWeight: 900 }}>{c.loyalty_points || 0} pts</span></td>
                                <td style={{ textAlign: 'right' }}>
                                    <button onClick={() => handleOpenModal(c)} className="ui-btn" style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.03)' }}>Editar</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {loading && <p className="text-center py-12 text-muted animate-pulse">Sincronizando directorio...</p>}
                </div>
            </section>

            <Modal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)}
                title={editingClient ? 'Editar Perfil' : 'Registro de Caballero'}
                actions={
                    <>
                                <button onClick={() => setIsModalOpen(false)} className="ui-btn" style={{ background: 'transparent' }}>Cancelar</button>
                                <button onClick={handleSubmit} className="ui-btn-gold" disabled={!editingClient && (!formData.password || formData.password.length < 8)}>Guardar Cliente</button>
                    </>
                }
            >
                <form className="space-y-4" onSubmit={handleSubmit} noValidate>
                    {errors._global && <div className="text-red-400">{errors._global}</div>}

                    <div className="grid grid-cols-2 gap-4">
                        <div className="group">
                            <label className="ui-kpi-label">Nombre</label>
                            <input 
                                className="ui-input" 
                                value={formData.first_name} 
                                onChange={e => setFormData({...formData, first_name: e.target.value})}
                                placeholder="Juan"
                                required
                            />
                        </div>
                        <div className="group">
                            <label className="ui-kpi-label">Apellido</label>
                            <input 
                                className="ui-input" 
                                value={formData.last_name} 
                                onChange={e => setFormData({...formData, last_name: e.target.value})}
                                placeholder="Pérez"
                                required
                            />
                        </div>
                    </div>

                    <div className="group">
                        <label className="ui-kpi-label">Email</label>
                        <input 
                            type="email"
                            className="ui-input" 
                            value={formData.email} 
                            onChange={e => setFormData({...formData, email: e.target.value})}
                            placeholder="juan@example.com"
                            disabled={!!editingClient}
                            required
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="group">
                            <label className="ui-kpi-label">Teléfono</label>
                            <input 
                                className="ui-input" 
                                value={formData.phone} 
                                onChange={e => setFormData({...formData, phone: e.target.value})}
                                placeholder="+52..."
                            />
                        </div>
                        <div className="group">
                            <label className="ui-kpi-label">Status VIP</label>
                            <select 
                                className="ui-input" 
                                value={formData.is_vip ? "true" : "false"}
                                onChange={e => setFormData({...formData, is_vip: e.target.value === "true"})}
                            >
                                <option value="false">No</option>
                                <option value="true">Sí</option>
                            </select>
                        </div>
                    </div>

                    {/* Password field only for new users */}
                    {!editingClient && (
                        <div className="group">
                            <label className="ui-kpi-label">Contraseña</label>
                            <div className="relative">
                                <div className="flex items-center gap-2">
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        className={`ui-input ${errors.password ? 'border-red-500' : ''}`}
                                        value={formData.password}
                                        onChange={e => { setFormData({...formData, password: e.target.value}); if (errors.password) setErrors({...errors, password: undefined}); calcStrength(e.target.value) }}
                                        placeholder="Mínimo 8 caracteres"
                                        required
                                    />
                                    <button type="button" className="ui-btn" style={{padding:'6px 8px'}} onClick={() => setShowPassword(!showPassword)}>{showPassword ? 'Ocultar' : 'Mostrar'}</button>
                                </div>
                                <div className="mt-2">
                                    <div className="w-full bg-gray-800 h-2 rounded overflow-hidden">
                                        <div style={{width: `${(passwordStrength/4)*100}%`}} className={`h-2 ${passwordStrength<=1?'bg-red-500':passwordStrength==2?'bg-yellow-400':'bg-green-400'} transition-all`}></div>
                                    </div>
                                    <div className="text-xs text-muted mt-1">Requisitos: 8+ caracteres, mayúscula, número, carácter especial</div>
                                    {errors.password && <div className="text-sm text-red-400 mt-1">{errors.password}</div>}
                                </div>
                            </div>
                        </div>
                    )}
                </form>
            </Modal>
        </div>
    )
}
