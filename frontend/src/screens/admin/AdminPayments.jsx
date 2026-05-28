import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'
import Modal from '../../components/Modal'
import StripeCardForm from '../../components/StripeCardForm'

const METHOD_LABELS = {
    cash: 'Efectivo', credit_card: 'T. Crédito', debit_card: 'T. Débito',
    mobile_payment: 'Pago Móvil', bank_transfer: 'Transferencia', stripe: 'Stripe'
}
const STATUS_COLORS = {
    completed: '#4ade80', pending: '#facc15', failed: '#f87171',
    refunded: '#60a5fa', processing: '#a78bfa'
}
const STATUS_ES = {
    completed: 'Completado', pending: 'Pendiente', failed: 'Fallido',
    refunded: 'Reembolsado', processing: 'Procesando'
}

function PaymentMethodSelector({ value, onChange }) {
    const methods = [
        { key: 'cash', icon: (
            <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2z" />
            </svg>
        ), label: 'Efectivo' },
        { key: 'credit_card', icon: (
            <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
        ), label: 'Crédito / Débito' },
        { key: 'mobile_payment', icon: (
            <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
        ), label: 'Pago Móvil' },
        { key: 'bank_transfer', icon: (
            <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
            </svg>
        ), label: 'Transferencia' },
    ]
    return (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
            {methods.map(m => (
                <button key={m.key} type="button" className={`method-btn ${value === m.key ? 'selected' : ''}`} onClick={() => onChange(m.key)}>
                    {m.icon}
                    <span>{m.label}</span>
                </button>
            ))}
        </div>
    )
}

function MiniChart({ data }) {
    if (!data?.length) return null
    const max = Math.max(...data, 1)
    return (
        <div className="chart-bar-wrap" style={{ marginTop: '0.75rem' }}>
            {data.map((v, i) => (
                <div key={i} className="chart-bar" style={{ height: `${Math.round((v / max) * 100)}%` }} />
            ))}
        </div>
    )
}

export default function AdminPayments() {
    const [payments, setPayments] = useState([])
    const [appointments, setAppointments] = useState([])
    const [loading, setLoading] = useState(true)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [processingStripe, setProcessingStripe] = useState(false)
    const [formData, setFormData] = useState({ appointment_id: '', amount: '', method: 'cash', tip: 0, notes: '' })

    const load = async () => {
        setLoading(true)
        try {
            const [pRes, aRes] = await Promise.all([
                apiFetch('/payments').then(r => r.json()),
                apiFetch('/appointments').then(r => r.json())
            ])
            const raw = Array.isArray(pRes) ? pRes : (pRes.data?.payments || pRes.data || [])
            setPayments(raw)
            setAppointments(aRes.data?.appointments || aRes.data || [])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [])

    const handleSubmit = async (e, cardData) => {
        if (e?.preventDefault) e.preventDefault()
        const payload = { ...formData, amount: parseFloat(formData.amount), tip: parseFloat(formData.tip) || 0 }

        if (formData.method === 'credit_card' && cardData) {
            setProcessingStripe(true)
            try {
                const res = await apiFetch('/payments/stripe/intent', {
                    method: 'POST',
                    body: JSON.stringify({ ...payload, card_last4: cardData.number.replace(/\s/g, '').slice(-4) })
                })
                if (res.ok) { setIsModalOpen(false); load(); toast.success('Pago con tarjeta procesado') }
                else { const err = await res.json(); toast.error(err.detail || 'Error al procesar tarjeta') }
            } finally { setProcessingStripe(false) }
            return
        }

        const res = await apiFetch('/payments', { method: 'POST', body: JSON.stringify(payload) })
        if (res.ok) { setIsModalOpen(false); load(); toast.success('Pago registrado correctamente') }
        else { const err = await res.json(); toast.error(err.detail || 'Error al registrar pago') }
    }

    const viewReceipt = (id) => window.open(`/api/payments/${id}/receipt`, '_blank')

    const totalRevenue = payments.filter(p => p.status === 'completed').reduce((s, p) => s + (p.amount || 0), 0)
    const totalTips = payments.filter(p => p.status === 'completed').reduce((s, p) => s + (p.tip || 0), 0)
    const pending = payments.filter(p => p.status === 'pending').length

    const last7 = Array.from({ length: 7 }, (_, i) => {
        const d = new Date(); d.setDate(d.getDate() - (6 - i))
        const ds = d.toISOString().slice(0, 10)
        return payments.filter(p => p.created_at?.startsWith(ds) && p.status === 'completed')
                       .reduce((s, p) => s + (p.amount || 0), 0)
    })

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Gestión de <span className="text-gold">Pagos</span></h2>
                    <p className="ui-profile-subtitle">Registro de transacciones y recibos</p>
                </div>
                <button onClick={() => setIsModalOpen(true)} className="ui-btn-gold">+ Registrar Pago</button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Ingresos Totales</p>
                    <p className="ui-kpi-value" style={{ color: '#4ade80' }}>${totalRevenue.toFixed(2)}</p>
                    <MiniChart data={last7} />
                </div>
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Propinas</p>
                    <p className="ui-kpi-value" style={{ color: 'var(--gold)' }}>${totalTips.toFixed(2)}</p>
                    <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div className="progress-bar-track" style={{ flex: 1 }}>
                            <div className="progress-bar-fill" style={{ width: totalRevenue ? `${Math.min(100, (totalTips / totalRevenue) * 400)}%` : '0%' }} />
                        </div>
                        <span style={{ fontSize: '10px', color: 'var(--muted)' }}>
                            {totalRevenue ? `${((totalTips / totalRevenue) * 100).toFixed(1)}%` : '0%'}
                        </span>
                    </div>
                </div>
                <div className="ui-kpi-card">
                    <p className="ui-kpi-label">Transacciones</p>
                    <p className="ui-kpi-value">{payments.length}</p>
                    {pending > 0 && <p style={{ marginTop: '0.5rem', fontSize: '10px', color: '#facc15' }}>{pending} pendiente{pending > 1 ? 's' : ''}</p>}
                </div>
            </div>

            <section className="ui-card-premium" style={{ padding: 0 }}>
                <div style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--gold)' }}>Historial</h3>
                    <span style={{ fontSize: '10px', color: 'var(--muted)' }}>{payments.length} registros</span>
                </div>
                <div className="ui-table-premium-wrapper">
                    <table className="ui-table-premium">
                        <thead>
                            <tr style={{ background: 'transparent' }}>
                                {['Cliente', 'Método', 'Monto', 'Propina', 'Estado', 'Fecha', ''].map((h, i) => (
                                    <th key={i} style={{ padding: '0.75rem 1.25rem', fontSize: '9px', color: '#3a3a3a', textTransform: 'uppercase', letterSpacing: '0.12em', fontWeight: 900, textAlign: i >= 2 && i <= 3 ? 'right' : i === 4 ? 'center' : 'left' }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {payments.map((p, i) => (
                                <tr key={p.id ?? i}>
                                    <td>
                                        <div style={{ fontWeight: 800, fontSize: '13px' }}>{p.customer_name || p.client_name || 'Cliente'}</div>
                                        <div style={{ fontSize: '10px', color: '#555' }}>#{p.invoice_number || (p.id?.slice(-6) ?? '------')}</div>
                                    </td>
                                    <td>
                                        <span style={{ fontSize: '10px', color: 'var(--muted)', background: 'rgba(255,255,255,0.03)', padding: '3px 8px', borderRadius: '6px', border: '1px solid var(--line)' }}>
                                            {METHOD_LABELS[p.method] || p.method || '–'}
                                        </span>
                                    </td>
                                    <td style={{ textAlign: 'right' }}>
                                        <span style={{ color: 'var(--gold)', fontWeight: 900, fontSize: '14px' }}>${(p.amount || 0).toFixed(2)}</span>
                                    </td>
                                    <td style={{ textAlign: 'right' }}>
                                        <span style={{ color: '#4ade80', fontSize: '12px' }}>{p.tip ? `+$${p.tip.toFixed(2)}` : '–'}</span>
                                    </td>
                                    <td style={{ textAlign: 'center' }}>
                                        <span className={`status-badge badge-${p.status || 'pending'}`}>
                                            {STATUS_ES[p.status] || p.status || 'Pendiente'}
                                        </span>
                                    </td>
                                    <td>
                                        <span style={{ color: 'var(--muted)', fontSize: '11px' }}>
                                            {p.created_at ? new Date(p.created_at).toLocaleDateString('es-MX', { day: '2-digit', month: 'short' }) : '–'}
                                        </span>
                                    </td>
                                    <td style={{ textAlign: 'right' }}>
                                        <button onClick={() => viewReceipt(p.id)} className="ui-btn" style={{ padding: '5px 10px', fontSize: '9px' }}>Recibo</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {loading && (
                        <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {[...Array(3)].map((_, i) => <div key={i} className="skeleton" style={{ height: '52px', opacity: 1 - i * 0.25 }} />)}
                        </div>
                    )}
                    {!loading && payments.length === 0 && (
                        <div style={{ padding: '4rem', textAlign: 'center' }}>
                            <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>💳</div>
                            <p style={{ fontWeight: 800 }}>Sin pagos registrados</p>
                            <p style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '0.5rem' }}>Registra el primer pago para verlo aquí</p>
                        </div>
                    )}
                </div>
            </section>

            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title="Registrar Pago"
                actions={formData.method !== 'credit_card' ? (
                    <>
                        <button onClick={() => setIsModalOpen(false)} className="ui-btn" style={{ background: 'transparent' }}>Cancelar</button>
                        <button onClick={handleSubmit} className="ui-btn-gold">Confirmar Pago</button>
                    </>
                ) : null}
            >
                <div className="space-y-5">
                    <div className="group">
                        <label className="ui-kpi-label">Cita</label>
                        <select className="ui-input" value={formData.appointment_id} onChange={e => setFormData({ ...formData, appointment_id: e.target.value })}>
                            <option value="">Seleccionar cita...</option>
                            {appointments.map(a => (
                                <option key={a.id} value={a.id}>{a.client_name || 'Cliente'} — {a.appointment_date} {a.start_time}</option>
                            ))}
                        </select>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div className="group">
                            <label className="ui-kpi-label">Monto ($)</label>
                            <input type="number" step="0.01" className="ui-input" value={formData.amount} onChange={e => setFormData({ ...formData, amount: e.target.value })} placeholder="0.00" />
                        </div>
                        <div className="group">
                            <label className="ui-kpi-label">Propina ($)</label>
                            <input type="number" step="0.01" className="ui-input" value={formData.tip} onChange={e => setFormData({ ...formData, tip: e.target.value })} placeholder="0.00" />
                        </div>
                    </div>
                    <div className="group">
                        <label className="ui-kpi-label" style={{ marginBottom: '0.75rem', display: 'block' }}>Método de Pago</label>
                        <PaymentMethodSelector value={formData.method} onChange={v => setFormData({ ...formData, method: v })} />
                    </div>
                    {formData.method === 'credit_card' && (
                        <div style={{ borderTop: '1px solid var(--line)', paddingTop: '1.5rem' }}>
                            <p style={{ fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--gold)', marginBottom: '1.25rem' }}>
                                Datos de Tarjeta
                            </p>
                            <StripeCardForm
                                amount={formData.amount ? parseFloat(formData.amount).toFixed(2) : null}
                                loading={processingStripe}
                                onSubmit={(cardData) => handleSubmit(null, cardData)}
                            />
                        </div>
                    )}
                    {formData.method !== 'credit_card' && (
                        <div className="group">
                            <label className="ui-kpi-label">Notas</label>
                            <textarea className="ui-input" value={formData.notes} onChange={e => setFormData({ ...formData, notes: e.target.value })} placeholder="Observaciones..." style={{ minHeight: '60px', resize: 'none' }} />
                        </div>
                    )}
                </div>
            </Modal>
        </div>
    )
}
