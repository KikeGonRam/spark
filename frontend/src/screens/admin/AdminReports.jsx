import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'

function SimpleBarChart({ data, labelKey, valueKey, color = 'var(--gold)' }) {
    const max = Math.max(...data.map(d => d[valueKey] || 0), 1)
    return (
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '6px', height: '120px', padding: '0 4px' }}>
            {data.map((d, i) => (
                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', height: '100%', justifyContent: 'flex-end' }}>
                    <span style={{ fontSize: '8px', color: '#555', fontWeight: 700 }}>{d[valueKey] || 0}</span>
                    <div style={{ width: '100%', background: color, borderRadius: '3px 3px 0 0', height: `${((d[valueKey] || 0) / max) * 80}%`, opacity: 0.85, minHeight: '4px', transition: 'height 0.4s' }} />
                    <span style={{ fontSize: '7px', color: '#444', textAlign: 'center', fontWeight: 700, overflow: 'hidden', maxWidth: '30px', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{d[labelKey]}</span>
                </div>
            ))}
        </div>
    )
}

export default function AdminReports() {
    const [revenue, setRevenue] = useState(null)
    const [appointments, setAppointments] = useState(null)
    const [loading, setLoading] = useState(true)
    const [period, setPeriod] = useState('month')

    const load = async () => {
        setLoading(true)
        try {
            const [rRes, aRes] = await Promise.all([
                apiFetch(`/reports/revenue?period=${period}`).then(r => r.json()),
                apiFetch(`/reports/appointments?period=${period}`).then(r => r.json()),
            ])
            setRevenue(rRes.data || rRes)
            setAppointments(aRes.data || aRes)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [period])

    const exportReport = async (type, format) => {
        try {
            const res = await apiFetch(`/reports/${type}/${format}`)
            if (res.ok) {
                const blob = await res.blob()
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `reporte-${type}.${format}`
                a.click()
                window.URL.revokeObjectURL(url)
            }
        } catch {
            toast.error('Error al generar el reporte')
        }
    }

    const revenueChartData = revenue?.by_day || revenue?.daily || []
    const appointmentChartData = appointments?.by_status || []

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end flex-wrap gap-4">
                <div>
                    <h2 className="ui-profile-title">Centro de <span className="text-gold">Reportes</span></h2>
                    <p className="ui-profile-subtitle">Análisis financiero y operativo</p>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    {['week', 'month', 'year'].map(p => (
                        <button key={p} onClick={() => setPeriod(p)} style={{ padding: '6px 14px', fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', borderRadius: '0.5rem', border: '1px solid', cursor: 'pointer', background: period === p ? 'var(--gold)' : 'transparent', color: period === p ? '#000' : 'var(--muted)', borderColor: period === p ? 'var(--gold)' : 'var(--line)' }}>
                            {p === 'week' ? 'Semana' : p === 'month' ? 'Mes' : 'Año'}
                        </button>
                    ))}
                </div>
            </div>

            {/* KPI Row */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Ingresos</p>
                    <p className="ui-kpi-value" style={{ color: '#4ade80' }}>${revenue?.total_revenue?.toFixed(2) || '0.00'}</p>
                </div>
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Total Citas</p>
                    <p className="ui-kpi-value">{appointments?.total || 0}</p>
                </div>
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Completadas</p>
                    <p className="ui-kpi-value" style={{ color: 'var(--gold)' }}>{appointments?.completed || 0}</p>
                </div>
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Promedio / Cita</p>
                    <p className="ui-kpi-value">${revenue?.average_per_appointment?.toFixed(2) || '0.00'}</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Revenue Chart */}
                <section className="ui-card-premium">
                    <div className="flex justify-between items-center mb-6">
                        <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em' }}>Ingresos del Período</h3>
                        <div style={{ display: 'flex', gap: '6px' }}>
                            <button onClick={() => exportReport('revenue', 'pdf')} className="ui-btn" style={{ padding: '5px 10px', background: 'rgba(239,68,68,0.1)', color: '#f87171', fontSize: '8px', border: '1px solid rgba(239,68,68,0.2)' }}>PDF</button>
                            <button onClick={() => exportReport('revenue', 'excel')} className="ui-btn" style={{ padding: '5px 10px', background: 'rgba(74,222,128,0.1)', color: '#4ade80', fontSize: '8px', border: '1px solid rgba(74,222,128,0.2)' }}>Excel</button>
                        </div>
                    </div>
                    {loading ? (
                        <div style={{ height: '120px', display: 'grid', placeItems: 'center' }}>
                            <p style={{ color: 'var(--muted)', fontSize: '12px' }} className="animate-pulse">Cargando datos...</p>
                        </div>
                    ) : revenueChartData.length > 0 ? (
                        <SimpleBarChart data={revenueChartData} labelKey="date" valueKey="revenue" color="var(--gold)" />
                    ) : (
                        <div style={{ height: '120px', display: 'grid', placeItems: 'center' }}>
                            <p style={{ color: 'var(--muted)', fontSize: '12px' }}>Sin datos para el período seleccionado</p>
                        </div>
                    )}
                </section>

                {/* Appointments Chart */}
                <section className="ui-card-premium">
                    <div className="flex justify-between items-center mb-6">
                        <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em' }}>Citas por Estado</h3>
                        <button onClick={() => exportReport('appointments', 'pdf')} className="ui-btn" style={{ padding: '5px 10px', background: 'rgba(239,68,68,0.1)', color: '#f87171', fontSize: '8px', border: '1px solid rgba(239,68,68,0.2)' }}>PDF</button>
                    </div>
                    {!loading && (
                        <div className="space-y-3">
                            {[
                                { key: 'completed', label: 'Completadas', color: '#4ade80' },
                                { key: 'cancelled', label: 'Canceladas', color: '#f87171' },
                                { key: 'pending', label: 'Pendientes', color: '#facc15' },
                                { key: 'no_show', label: 'No asistió', color: '#a78bfa' },
                            ].map(({ key, label, color }) => {
                                const count = appointments?.[key] || 0
                                const total = appointments?.total || 1
                                const pct = Math.round((count / total) * 100)
                                return (
                                    <div key={key}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span style={{ fontSize: '10px', color: '#aaa', fontWeight: 700 }}>{label}</span>
                                            <span style={{ fontSize: '10px', fontWeight: 900, color }}>{count} ({pct}%)</span>
                                        </div>
                                        <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: '99px', height: '5px' }}>
                                            <div style={{ background: color, borderRadius: '99px', height: '100%', width: `${pct}%`, transition: 'width 0.4s' }} />
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </section>
            </div>

            {/* Top Services Table */}
            <section className="ui-card-premium">
                <div className="flex justify-between items-center mb-6">
                    <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em' }}>Servicios Más Solicitados</h3>
                    <button onClick={() => exportReport('services', 'pdf')} className="ui-btn" style={{ padding: '5px 10px', background: 'rgba(239,68,68,0.1)', color: '#f87171', fontSize: '8px', border: '1px solid rgba(239,68,68,0.2)' }}>Exportar</button>
                </div>
                <div className="ui-table-premium-wrapper">
                <table className="ui-table-premium">
                    <thead>
                        <tr style={{ background: 'transparent' }}>
                            <th style={{ textAlign: 'left', padding: '0.75rem', fontSize: '9px', color: '#444', textTransform: 'uppercase' }}>#</th>
                            <th style={{ textAlign: 'left', padding: '0.75rem', fontSize: '9px', color: '#444', textTransform: 'uppercase' }}>Servicio</th>
                            <th style={{ textAlign: 'center', padding: '0.75rem', fontSize: '9px', color: '#444', textTransform: 'uppercase' }}>Citas</th>
                            <th style={{ textAlign: 'right', padding: '0.75rem', fontSize: '9px', color: '#444', textTransform: 'uppercase' }}>Ingresos</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(revenue?.top_services || []).map((s, i) => (
                            <tr key={i}>
                                <td><span style={{ fontWeight: 900, color: 'var(--gold)' }}>#{i + 1}</span></td>
                                <td><span style={{ fontWeight: 800 }}>{s.name || s.service_name}</span></td>
                                <td style={{ textAlign: 'center' }}><span style={{ color: 'var(--muted)' }}>{s.count || 0}</span></td>
                                <td style={{ textAlign: 'right' }}><span className="text-gold font-bold">${(s.revenue || 0).toFixed(2)}</span></td>
                            </tr>
                        ))}
                        {(!revenue?.top_services || revenue.top_services.length === 0) && !loading && (
                            <tr><td colSpan={4} style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>Sin datos disponibles</td></tr>
                        )}
                    </tbody>
                </table>
                </div>
            </section>
        </div>
    )
}
