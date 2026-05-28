import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'

const ACTION_COLORS = {
    create: '#4ade80', created: '#4ade80',
    update: '#facc15', updated: '#facc15',
    delete: '#f87171', deleted: '#f87171',
    login: '#60a5fa', logout: '#a78bfa',
    payment: 'var(--gold)',
}

export default function AdminLogs() {
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('')
    const [page, setPage] = useState(1)
    const PER_PAGE = 20

    const load = async () => {
        setLoading(true)
        try {
            const res = await apiFetch(`/logs?limit=100`)
            const data = await res.json()
            setLogs(data.data?.logs || data.data || [])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [])

    const filtered = filter
        ? logs.filter(l =>
            (l.description || '').toLowerCase().includes(filter.toLowerCase()) ||
            (l.event || l.action || '').toLowerCase().includes(filter.toLowerCase()) ||
            (l.causer_name || l.user_name || '').toLowerCase().includes(filter.toLowerCase())
        )
        : logs

    const paginated = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE)
    const totalPages = Math.ceil(filtered.length / PER_PAGE)

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end flex-wrap gap-4">
                <div>
                    <h2 className="ui-profile-title">Registros de <span className="text-gold">Actividad</span></h2>
                    <p className="ui-profile-subtitle">Historial de acciones del sistema</p>
                </div>
                <button onClick={load} className="ui-btn" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--line)', color: '#fff', fontSize: '9px' }}>↺ Actualizar</button>
            </div>

            <div className="group" style={{ maxWidth: '400px' }}>
                <input
                    className="ui-input"
                    value={filter}
                    onChange={e => { setFilter(e.target.value); setPage(1) }}
                    placeholder="Buscar por acción, usuario, descripción..."
                    style={{ fontSize: '13px' }}
                />
            </div>

            <section className="ui-card-premium">
                <div className="ui-table-premium-wrapper">
                <table className="ui-table-premium">
                    <thead>
                        <tr style={{ background: 'transparent' }}>
                            <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '9px', color: '#444', textTransform: 'uppercase' }}>Fecha</th>
                            <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '9px', color: '#444', textTransform: 'uppercase' }}>Usuario</th>
                            <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '9px', color: '#444', textTransform: 'uppercase' }}>Acción</th>
                            <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '9px', color: '#444', textTransform: 'uppercase' }}>Descripción</th>
                            <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '9px', color: '#444', textTransform: 'uppercase' }}>Módulo</th>
                        </tr>
                    </thead>
                    <tbody>
                        {paginated.map((log, i) => {
                            const action = (log.event || log.action || '').toLowerCase()
                            const actionColor = Object.keys(ACTION_COLORS).find(k => action.includes(k))
                            return (
                                <tr key={log.id || i}>
                                    <td>
                                        <span style={{ fontSize: '10px', color: 'var(--muted)', fontFamily: 'monospace' }}>
                                            {log.created_at ? new Date(log.created_at).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' }) : '-'}
                                        </span>
                                    </td>
                                    <td>
                                        <span style={{ fontWeight: 800, fontSize: '12px' }}>{log.causer_name || log.user_name || log.causer?.name || 'Sistema'}</span>
                                    </td>
                                    <td>
                                        <span style={{ fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', color: ACTION_COLORS[actionColor] || '#fff', background: `${ACTION_COLORS[actionColor] || '#ffffff'}15`, padding: '3px 8px', borderRadius: '99px' }}>
                                            {log.event || log.action || 'info'}
                                        </span>
                                    </td>
                                    <td>
                                        <span style={{ fontSize: '12px', color: '#aaa' }}>{log.description || log.message || '-'}</span>
                                    </td>
                                    <td>
                                        <span style={{ fontSize: '10px', color: '#555' }}>{log.subject_type || log.module || '-'}</span>
                                    </td>
                                </tr>
                            )
                        })}
                    </tbody>
                </table>

                {loading && <p className="text-center py-12 text-muted animate-pulse">Cargando registros...</p>}
                {!loading && paginated.length === 0 && <p className="text-center py-12" style={{ color: 'var(--muted)' }}>Sin registros encontrados.</p>}

                {totalPages > 1 && (
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--line)' }}>
                        <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} style={{ padding: '6px 14px', background: 'transparent', border: '1px solid var(--line)', color: page === 1 ? '#333' : '#fff', borderRadius: '0.5rem', cursor: page === 1 ? 'default' : 'pointer', fontSize: '11px' }}>← Ant</button>
                        <span style={{ padding: '6px 12px', fontSize: '11px', color: 'var(--muted)' }}>{page} / {totalPages}</span>
                        <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} style={{ padding: '6px 14px', background: 'transparent', border: '1px solid var(--line)', color: page === totalPages ? '#333' : '#fff', borderRadius: '0.5rem', cursor: page === totalPages ? 'default' : 'pointer', fontSize: '11px' }}>Sig →</button>
                    </div>
                )}
                </div>
            </section>

            <div style={{ display: 'flex', gap: '1rem', fontSize: '10px', color: '#444', flexWrap: 'wrap' }}>
                {Object.entries(ACTION_COLORS).slice(0, 6).map(([k, c]) => (
                    <div key={k} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: c }} />
                        <span style={{ textTransform: 'capitalize' }}>{k}</span>
                    </div>
                ))}
            </div>
        </div>
    )
}
