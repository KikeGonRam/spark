import { useEffect, useState } from 'react'
import { Badge } from '../../components/UI'
import { apiFetch, navigate, getStoredUser } from '../../hooks/useNavigation'

export default function ClientOverview({ summary, health }) {
    const [client, setClient] = useState(null)

    useEffect(() => {
        const load = async () => {
            const stored = getStoredUser()
            if (!stored || stored.role !== 'client') return
            const res = await apiFetch('/clients/me')
            const data = await res.json()
            if (res.ok) setClient(data.data?.client || null)
        }
        load()
    }, [])

    const stats = [
        { label: 'Mis Citas', value: client?.total_appointments ?? '0', icon: '📅' },
        { label: 'Servicios', value: client?.completed_appointments ?? '0', icon: '✂️' },
        { label: 'Puntos Elite', value: client?.loyalty_points ?? '0', icon: '💎' },
        { label: 'Nivel', value: client?.is_vip ? 'VIP' : 'Cliente', icon: '🏆' }
    ]

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="ui-profile-title">Mi <span className="text-gold">Club Elite</span></h2>
                    <p className="ui-profile-subtitle">Gestiona tu experiencia premium en BarberPro.</p>
                </div>
                <button onClick={() => navigate('/dashboard/client/booking')} className="ui-btn-gold">
                    Agendar Cita Premium
                </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat, i) => (
                    <div key={i} className="ui-kpi-card group">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="ui-kpi-label">{stat.label}</p>
                                <p className="ui-kpi-value">{stat.value}</p>
                            </div>
                            <div className="h-8 w-8 rounded-lg bg-white/5 flex items-center justify-center">
                                <span style={{ fontSize: '1.2rem' }}>{stat.icon}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <section className="ui-card-premium">
                    <h3 className="text-xs font-black uppercase text-white mb-6">Estado de Fidelidad</h3>
                    <div className="space-y-4">
                        <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-muted">
                            <span>Próximo Beneficio: {client?.is_vip ? 'Prioridad VIP' : 'Ritual de Barba Gratis'}</span>
                            <span className="text-gold">{client?.loyalty_points ? Math.min(100, Math.round((client.loyalty_points / 1000) * 100)) : 0}%</span>
                        </div>
                        <div style={{ height: '6px', width: '100%', background: 'rgba(255,255,255,0.05)', borderRadius: '99px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${client?.loyalty_points ? Math.min(100, Math.round((client.loyalty_points / 1000) * 100)) : 0}%`, background: 'var(--gold)' }}></div>
                        </div>
                        <p className="text-[11px] text-muted italic">{client ? `Código de referido: ${client.referral_code || '-'}` : 'Cargando perfil...'}</p>
                    </div>
                </section>

                <section className="ui-card-premium">
                    <h3 className="text-xs font-black uppercase text-white mb-6">Estado del Sistema</h3>
                    <div className="flex items-center gap-3">
                        <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                        <p className="text-[10px] text-muted uppercase font-black">{health}</p>
                    </div>
                </section>
            </div>
        </div>
    )
}
