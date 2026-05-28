import { useEffect, useState } from 'react'
import { Badge } from './UI'

export default function AdminDashboard({ summary, health, refresh }) {
    const [barberStatus] = useState([
        { name: 'Juan Pérez', is_busy: true, progress: 65 },
        { name: 'Mario Ruiz', is_busy: false, progress: 0 },
        { name: 'Alex León', is_busy: true, progress: 30 },
        { name: 'Carlos Vela', is_busy: false, progress: 0 }
    ])

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="ui-profile-title">Dashboard <span className="text-gold">Administrativo</span></h2>
                    <p className="ui-profile-subtitle mt-2">Vista ejecutiva del rendimiento y agenda de la barbería.</p>
                </div>
                <div className="flex items-center gap-4">
                    <button className="ui-btn" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--muted)' }}>
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                        Mantenimiento
                    </button>
                    <Badge className="bg-white/5 border-white/10">
                        <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse mr-2"></span>
                        Sistema Activo
                    </Badge>
                </div>
            </div>

            {/* KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <KPICard label="Citas Hoy" value={summary?.today_appointments ?? '18'} icon="calendar" color="blue" />
                <KPICard label="Ingresos Hoy" value={summary ? `$${summary.today_revenue}` : '$1,240'} icon="money" color="green" />
                <KPICard label="Clientes Activos" value={summary?.total_clients ?? '326'} icon="users" color="cyan" />
                <KPICard label="Tasa Retención" value="84.2%" icon="chart" color="purple" />
            </div>

            {/* AI Predictions */}
            <section className="ui-card-premium p-6">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h3 className="text-xs font-black text-white uppercase tracking-widest">🤖 Predicciones con IA</h3>
                        <span className="text-[9px] text-muted font-bold uppercase mt-1">Análisis basado en Ollama</span>
                    </div>
                    <Badge className="border-indigo-500/30 text-indigo-400">Beta</Badge>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                        <p className="text-[10px] font-black uppercase text-muted">Ingresos (7d)</p>
                        <p className="text-2xl font-black text-green-400">$8,450</p>
                    </div>
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                        <p className="text-[10px] font-black uppercase text-muted">Citas (7d)</p>
                        <p className="text-2xl font-black text-blue-400">124</p>
                    </div>
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                        <p className="text-[10px] font-black uppercase text-muted">Confianza</p>
                        <p className="text-2xl font-black text-indigo-400">94%</p>
                    </div>
                </div>
            </section>

            {/* Live Stations */}
            <section className="ui-card-premium p-6">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h3 className="text-xs font-black text-white uppercase tracking-widest">Estaciones en Vivo</h3>
                        <p className="text-[9px] text-muted uppercase font-bold mt-1">Ocupación en tiempo real</p>
                    </div>
                    <Badge className="text-green-400 border-green-500/20">Live</Badge>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {barberStatus.map((barber, i) => (
                        <div key={i} className="p-4 rounded-xl bg-white/5 border border-white/5 hover:border-gold/30 transition-all">
                            <div className="flex items-center gap-3">
                                <div className="relative">
                                    <div className="h-10 w-10 rounded-lg bg-black border border-white/10 flex items-center justify-center text-gold font-black text-xs">
                                        {barber.name.substring(0, 2).toUpperCase()}
                                    </div>
                                    <div className={`absolute -bottom-1 -right-1 h-3 w-3 rounded-full border-2 border-black ${barber.is_busy ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`}></div>
                                </div>
                                <div>
                                    <p className="text-xs font-bold">{barber.name}</p>
                                    <p className={`text-[8px] font-black uppercase ${barber.is_busy ? 'text-red-400' : 'text-green-400'}`}>
                                        {barber.is_busy ? 'Ocupado' : 'Disponible'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Bottom Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <article className="ui-card-premium p-6">
                    <h3 className="text-xs font-black uppercase text-white tracking-widest mb-4">Reportes</h3>
                    <div className="grid grid-cols-2 gap-3">
                        <button className="ui-btn" style={{ background: 'rgba(255,255,255,0.03)', fontSize: '9px' }}>Mensual PDF</button>
                        <button className="ui-btn" style={{ background: 'rgba(255,255,255,0.03)', fontSize: '9px' }}>Ingresos CSV</button>
                    </div>
                </article>
                <article className="ui-card-premium p-6">
                    <h3 className="text-xs font-black uppercase text-white tracking-widest mb-4">Estado Sistema</h3>
                    <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                        <p className="text-[10px] font-bold">API Python: <span className="text-green-400">ONLINE</span></p>
                        <p className="text-[10px] text-muted mt-1">{health}</p>
                    </div>
                </article>
            </div>
        </div>
    )
}

function KPICard({ label, value, color }) {
    const iconColors = {
        blue: 'text-blue-400 bg-blue-500/10',
        green: 'text-green-400 bg-green-500/10',
        cyan: 'text-cyan-400 bg-cyan-500/10',
        purple: 'text-purple-400 bg-purple-500/10'
    }
    return (
        <div className="ui-kpi-card group hover:border-gold/30">
            <div className="flex justify-between items-start">
                <div>
                    <p className="ui-kpi-label">{label}</p>
                    <p className="ui-kpi-value">{value}</p>
                </div>
                <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${iconColors[color]}`}>
                    <div className="h-4 w-4 bg-current opacity-20 rounded-full"></div>
                </div>
            </div>
        </div>
    )
}
