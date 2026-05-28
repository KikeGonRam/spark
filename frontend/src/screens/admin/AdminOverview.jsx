import { useEffect, useState } from 'react'
import { Badge } from '../../components/UI'
import { apiFetch } from '../../hooks/useNavigation'

function MiniLine({ values, color = 'var(--gold)' }) {
    if (!values?.length) return null
    const max = Math.max(...values, 1)
    const w = 100
    const h = 40
    const pts = values.map((v, i) => `${(i / (values.length - 1)) * w},${h - (v / max) * (h - 4)}`).join(' ')
    return (
        <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', height: '40px' }} preserveAspectRatio="none">
            <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
        </svg>
    )
}

export default function AdminOverview({ summary, health }) {
    const [stats, setStats] = useState(null)
    const [alerts, setAlerts] = useState([])
    const [revenueWeek, setRevenueWeek] = useState([])
    const [loadingStats, setLoadingStats] = useState(true)

    useEffect(() => {
        const load = async () => {
            try {
                const [sRes, aRes, rRes] = await Promise.all([
                    apiFetch('/admin/dashboard/stats').then(r => r.json()),
                    apiFetch('/admin/dashboard/alerts').then(r => r.json()),
                    apiFetch('/reports/revenue?period=week').then(r => r.json()),
                ])
                setStats(sRes.data || sRes)
                setAlerts(aRes.data?.alerts || aRes.data || [])
                const daily = (rRes.data?.by_day || rRes.data?.daily || [])
                setRevenueWeek(daily.map(d => d.revenue || 0))
            } catch {
                // fallback to summary prop
            } finally {
                setLoadingStats(false)
            }
        }
        load()
    }, [])

    const kpis = [
        { label: 'Citas Hoy', value: stats?.today_appointments ?? summary?.today_appointments ?? '—', color: 'blue', trend: revenueWeek },
        { label: 'Ingresos Hoy', value: stats?.today_revenue != null ? `$${stats.today_revenue}` : summary?.today_revenue != null ? `$${summary.today_revenue}` : '—', color: 'green', trend: revenueWeek },
        { label: 'Clientes Totales', value: stats?.total_clients ?? summary?.total_clients ?? '—', color: 'cyan', trend: [] },
        { label: 'Tasa Ocupación', value: stats?.occupancy_rate != null ? `${stats.occupancy_rate}%` : '—', color: 'purple', trend: [] },
    ]

    const colorMap = { blue: '#60a5fa', green: '#4ade80', cyan: '#22d3ee', purple: '#a78bfa' }

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center flex-wrap gap-4">
                <div>
                    <h2 className="ui-profile-title">Vista <span className="text-gold">General</span></h2>
                    <p className="ui-profile-subtitle">Rendimiento en tiempo real de la barbería</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#4ade80' }} className="animate-pulse" />
                    <span style={{ fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', color: '#4ade80' }}>En Vivo</span>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {kpis.map((k, i) => (
                    <div key={i} className="ui-kpi-card group hover:border-gold/30" style={{ position: 'relative', overflow: 'hidden' }}>
                        <p className="ui-kpi-label">{k.label}</p>
                        <p className="ui-kpi-value" style={{ color: colorMap[k.color] }}>{loadingStats ? '...' : k.value}</p>
                        {k.trend?.length > 1 && (
                            <div style={{ marginTop: '12px', opacity: 0.4 }}>
                                <MiniLine values={k.trend} color={colorMap[k.color]} />
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Revenue Week Chart */}
                <section className="ui-card-premium lg:col-span-2">
                    <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem' }}>Ingresos — Últimos 7 Días</h3>
                    {revenueWeek.length > 1 ? (
                        <div style={{ height: '100px', display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
                            {revenueWeek.map((v, i) => {
                                const max = Math.max(...revenueWeek, 1)
                                return (
                                    <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', height: '100%', justifyContent: 'flex-end' }}>
                                        <span style={{ fontSize: '8px', color: '#555' }}>${v}</span>
                                        <div style={{ width: '100%', background: 'var(--gold)', borderRadius: '3px 3px 0 0', height: `${(v / max) * 72}%`, minHeight: '4px', opacity: 0.85 }} />
                                    </div>
                                )
                            })}
                        </div>
                    ) : (
                        <p style={{ color: 'var(--muted)', fontSize: '12px', padding: '2rem 0', textAlign: 'center' }}>Sin datos de ingresos aún</p>
                    )}
                </section>

                {/* Alerts & Status */}
                <section className="ui-card-premium">
                    <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem' }}>Estado del Sistema</h3>
                    <div className="space-y-3">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', background: 'rgba(255,255,255,0.02)', borderRadius: '0.5rem' }}>
                            <div>
                                <p style={{ fontSize: '11px', fontWeight: 800 }}>API Backend</p>
                                <p style={{ fontSize: '9px', color: 'var(--muted)' }}>{health}</p>
                            </div>
                            <Badge className="text-green-400 border-green-500/20">Online</Badge>
                        </div>

                        {alerts.slice(0, 3).map((a, i) => (
                            <div key={i} style={{ padding: '0.75rem', background: 'rgba(248,113,113,0.05)', border: '1px solid rgba(248,113,113,0.15)', borderRadius: '0.5rem' }}>
                                <p style={{ fontSize: '11px', fontWeight: 800, color: '#f87171' }}>{a.title || a.type}</p>
                                <p style={{ fontSize: '9px', color: '#888', marginTop: '2px' }}>{a.message || a.description}</p>
                            </div>
                        ))}

                        {alerts.length === 0 && !loadingStats && (
                            <p style={{ fontSize: '11px', color: 'var(--muted)', padding: '0.5rem' }}>Sin alertas críticas</p>
                        )}
                    </div>
                </section>
            </div>

            {/* Quick Stats Row */}
            {stats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                        { label: 'Citas Esta Semana', value: stats.week_appointments ?? '—' },
                        { label: 'Barberos Activos', value: stats.active_barbers ?? '—' },
                        { label: 'Ingresos del Mes', value: stats.month_revenue != null ? `$${stats.month_revenue}` : '—' },
                        { label: 'Stock Bajo', value: stats.low_stock_count ?? '0', warn: (stats.low_stock_count || 0) > 0 },
                    ].map((s, i) => (
                        <div key={i} className="ui-kpi-card" style={{ borderColor: s.warn ? 'rgba(248,113,113,0.3)' : 'var(--line)' }}>
                            <p className="ui-kpi-label">{s.label}</p>
                            <p style={{ marginTop: '0.5rem', fontSize: '1.5rem', fontWeight: 900, color: s.warn ? '#f87171' : '#fff' }}>{s.value}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
