import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'

const TYPE_ICONS = {
    appointment: '📅',
    payment: '💰',
    reminder: '⏰',
    system: '⚙️',
    promotion: '🎁',
    default: '🔔'
}

const TYPE_COLORS = {
    appointment: '#60a5fa',
    payment: '#4ade80',
    reminder: '#facc15',
    system: '#a78bfa',
    promotion: 'var(--gold)',
}

export default function ClientNotifications() {
    const [notifications, setNotifications] = useState([])
    const [loading, setLoading] = useState(true)

    const load = async () => {
        setLoading(true)
        try {
            const res = await apiFetch('/notifications')
            const data = await res.json()
            setNotifications(Array.isArray(data) ? data : (data.data?.notifications || data.data || []))
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [])

    const markRead = async (id) => {
        await apiFetch(`/notifications/${id}/read`, { method: 'POST' })
        setNotifications(prev => prev.map(n => n.id === id ? { ...n, read_at: new Date().toISOString() } : n))
    }

    const markAllRead = async () => {
        await apiFetch('/notifications/read-all', { method: 'POST' })
        setNotifications(prev => prev.map(n => ({ ...n, read_at: n.read_at || new Date().toISOString() })))
    }

    const unreadCount = notifications.filter(n => !(n.read_at || n.read)).length

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Mis <span className="text-gold">Notificaciones</span></h2>
                    <p className="ui-profile-subtitle" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {unreadCount > 0 ? (
                            <>
                                <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: 'var(--gold)', color: '#000', borderRadius: '50%', width: '20px', height: '20px', fontSize: '10px', fontWeight: 900 }}>{unreadCount}</span>
                                sin leer
                            </>
                        ) : 'Todo al día'}
                    </p>
                </div>
                {unreadCount > 0 && (
                    <button onClick={markAllRead} className="ui-btn" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--line)', color: '#fff', fontSize: '9px' }}>
                        ✓ Marcar todas como leídas
                    </button>
                )}
            </div>

            {loading && <p className="text-center py-12 text-muted animate-pulse">Cargando notificaciones...</p>}

            {!loading && notifications.length === 0 && (
                <div className="ui-card-premium text-center" style={{ padding: '4rem' }}>
                    <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔔</div>
                    <p style={{ fontWeight: 800, fontSize: '16px' }}>Sin notificaciones</p>
                    <p style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '0.5rem' }}>Te avisaremos cuando haya algo importante</p>
                </div>
            )}

            <div className="space-y-3">
                {notifications.map(n => {
                    const isRead = !!n.read_at
                    const type = n.type || n.notification_type || 'default'
                    const color = TYPE_COLORS[type] || '#fff'
                    const icon = TYPE_ICONS[type] || TYPE_ICONS.default
                    return (
                        <div
                            key={n.id}
                            onClick={() => !isRead && markRead(n.id)}
                            className="ui-card-premium"
                            style={{
                                padding: '1.25rem',
                                display: 'flex',
                                gap: '1rem',
                                alignItems: 'flex-start',
                                cursor: isRead ? 'default' : 'pointer',
                                opacity: isRead ? 0.6 : 1,
                                borderLeft: `3px solid ${isRead ? 'var(--line)' : color}`,
                                transition: 'opacity 0.2s'
                            }}
                        >
                            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: `${color}15`, display: 'grid', placeItems: 'center', flexShrink: 0 }}>
                                <span style={{ fontSize: '1.2rem' }}>{icon}</span>
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', marginBottom: '4px' }}>
                                    <p style={{ fontWeight: 800, fontSize: '14px' }}>{n.title || 'Notificación'}</p>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                                        {!isRead && (
                                            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: color }} />
                                        )}
                                        <span style={{ fontSize: '9px', color: '#555' }}>
                                            {n.created_at ? new Date(n.created_at).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' }) : '-'}
                                        </span>
                                    </div>
                                </div>
                                <p style={{ fontSize: '12px', color: 'var(--muted)', lineHeight: 1.5 }}>{n.message || n.body || n.data?.message || ''}</p>
                                {n.action_url && (
                                    <a href={n.action_url} style={{ fontSize: '10px', color: color, fontWeight: 800, marginTop: '6px', display: 'inline-block' }}>
                                        Ver detalles →
                                    </a>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
