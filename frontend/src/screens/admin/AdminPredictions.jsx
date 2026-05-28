import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'

function MiniBarChart({ bars, color = 'var(--gold)' }) {
    const max = Math.max(...bars.map(b => b.value || 0), 1)
    return (
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '4px', height: '80px' }}>
            {bars.map((b, i) => (
                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px', height: '100%', justifyContent: 'flex-end' }}>
                    <div style={{ width: '100%', background: color, borderRadius: '2px 2px 0 0', height: `${(b.value / max) * 65}%`, minHeight: '3px', opacity: 0.8 }} />
                    <span style={{ fontSize: '7px', color: '#444', textAlign: 'center', maxWidth: '24px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.label}</span>
                </div>
            ))}
        </div>
    )
}

export default function AdminPredictions() {
    const [income, setIncome] = useState(null)
    const [peakHours, setPeakHours] = useState(null)
    const [services, setServices] = useState(null)
    const [insights, setInsights] = useState(null)
    const [loading, setLoading] = useState(true)
    const [days, setDays] = useState(30)

    const load = async () => {
        setLoading(true)
        try {
            const [iRes, pRes, sRes, insRes] = await Promise.all([
                apiFetch(`/predictions/income/${days}`).then(r => r.json()),
                apiFetch('/predictions/peak-hours').then(r => r.json()),
                apiFetch('/predictions/services').then(r => r.json()),
                apiFetch('/predictions/insights').then(r => r.json()),
            ])
            setIncome(iRes.data || iRes)
            setPeakHours(pRes.data || pRes)
            setServices(sRes.data || sRes)
            setInsights(insRes.data || insRes)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [days])

    const peakData = peakHours?.hours?.map(h => ({ label: `${h.hour}h`, value: h.count || h.appointments || 0 })) || []
    const svcList = services?.top_services ?? (Array.isArray(services) ? services : []);
    const serviceData = (Array.isArray(svcList) ? svcList : []).slice(0, 8).map(s => ({ label: s.name?.slice(0, 6) || 'Srv', value: s.predicted_count || s.count || 0 }))

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end flex-wrap gap-4">
                <div>
                    <h2 className="ui-profile-title">Predicciones <span className="text-gold">IA</span></h2>
                    <p className="ui-profile-subtitle">Pronósticos y análisis predictivo del negocio</p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                    {[7, 14, 30, 60].map(d => (
                        <button key={d} onClick={() => setDays(d)} style={{ padding: '6px 12px', fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', borderRadius: '0.5rem', border: '1px solid', cursor: 'pointer', background: days === d ? 'var(--gold)' : 'transparent', color: days === d ? '#000' : 'var(--muted)', borderColor: days === d ? 'var(--gold)' : 'var(--line)' }}>
                            {d}d
                        </button>
                    ))}
                </div>
            </div>

            {/* Income Prediction */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="ui-kpi-card" style={{ borderColor: 'rgba(212,175,55,0.2)' }}>
                    <p className="ui-kpi-label">Ingreso Proyectado</p>
                    <p className="ui-kpi-value" style={{ color: 'var(--gold)' }}>
                        {loading ? '...' : `$${(income?.predicted_income || income?.total || 0).toLocaleString()}`}
                    </p>
                    <p style={{ fontSize: '9px', color: 'var(--muted)', marginTop: '4px' }}>Próximos {days} días</p>
                </div>
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Citas Esperadas</p>
                    <p className="ui-kpi-value">{loading ? '...' : income?.predicted_appointments || '-'}</p>
                    <p style={{ fontSize: '9px', color: 'var(--muted)', marginTop: '4px' }}>Basado en historial</p>
                </div>
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Confianza del Modelo</p>
                    <p className="ui-kpi-value" style={{ color: '#4ade80' }}>{loading ? '...' : `${income?.confidence || 78}%`}</p>
                    <p style={{ fontSize: '9px', color: 'var(--muted)', marginTop: '4px' }}>Precisión estimada</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Peak Hours */}
                <section className="ui-card-premium">
                    <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem' }}>Horas Pico</h3>
                    {loading ? (
                        <div style={{ height: '80px', display: 'grid', placeItems: 'center' }}>
                            <p style={{ color: 'var(--muted)', fontSize: '11px' }} className="animate-pulse">Calculando...</p>
                        </div>
                    ) : peakData.length > 0 ? (
                        <MiniBarChart bars={peakData} color="#60a5fa" />
                    ) : (
                        <p style={{ color: 'var(--muted)', fontSize: '12px', padding: '2rem 0' }}>Sin datos suficientes</p>
                    )}
                    {peakHours?.busiest_hour && (
                        <p style={{ marginTop: '1rem', fontSize: '10px', color: 'var(--muted)' }}>
                            Hora más concurrida: <span style={{ color: 'var(--gold)', fontWeight: 900 }}>{peakHours.busiest_hour}:00 hrs</span>
                        </p>
                    )}
                </section>

                {/* Top Services Prediction */}
                <section className="ui-card-premium">
                    <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem' }}>Servicios Proyectados</h3>
                    {loading ? (
                        <div style={{ height: '80px', display: 'grid', placeItems: 'center' }}>
                            <p style={{ color: 'var(--muted)', fontSize: '11px' }} className="animate-pulse">Calculando...</p>
                        </div>
                    ) : serviceData.length > 0 ? (
                        <MiniBarChart bars={serviceData} color="var(--gold)" />
                    ) : (
                        <p style={{ color: 'var(--muted)', fontSize: '12px', padding: '2rem 0' }}>Sin datos suficientes</p>
                    )}
                </section>
            </div>

            {/* Insights */}
            <section className="ui-card-premium">
                <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '1.5rem' }}>Recomendaciones del Sistema</h3>
                {loading ? (
                    <p style={{ color: 'var(--muted)', fontSize: '12px' }} className="animate-pulse">Generando insights...</p>
                ) : (
                    <div className="space-y-3">
                        {(insights?.recommendations || insights?.insights || []).map((rec, i) => (
                            <div key={i} style={{ padding: '1rem', background: 'rgba(212,175,55,0.04)', border: '1px solid rgba(212,175,55,0.1)', borderRadius: '0.75rem', display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                                <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'rgba(212,175,55,0.15)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
                                    <span style={{ color: 'var(--gold)', fontSize: '12px', fontWeight: 900 }}>{i + 1}</span>
                                </div>
                                <div>
                                    {rec.title && <p style={{ fontWeight: 800, fontSize: '13px', marginBottom: '4px' }}>{rec.title}</p>}
                                    <p style={{ fontSize: '12px', color: 'var(--muted)' }}>{rec.message || rec.text || rec}</p>
                                </div>
                            </div>
                        ))}
                        {(!insights?.recommendations?.length && !insights?.insights?.length) && (
                            <p style={{ color: 'var(--muted)', fontSize: '12px' }}>Sin recomendaciones disponibles aún. El sistema necesita más datos para generar predicciones.</p>
                        )}
                    </div>
                )}
            </section>
        </div>
    )
}
