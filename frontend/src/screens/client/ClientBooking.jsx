import { useState, useEffect } from 'react'
import { apiFetch, navigate, getStoredUser } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'
import StripeCardForm from '../../components/StripeCardForm'

const TIMES = [
    '09:00','09:30','10:00','10:30','11:00','11:30',
    '12:00','12:30','13:00','14:00','14:30','15:00',
    '15:30','16:00','16:30','17:00','17:30','18:00',
    '18:30','19:00','19:30','20:00',
]

const STEP_LABELS = ['Servicio', 'Maestro', 'Fecha y Hora', 'Pago']

function StepIndicator({ current }) {
    return (
        <div className="step-indicator">
            {STEP_LABELS.map((label, i) => (
                <>
                    <div key={`dot-${i}`} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
                        <div className={`step-dot ${i < current ? 'done' : i === current ? 'active' : 'pending'}`}>
                            {i < current ? '✓' : i + 1}
                        </div>
                        <span className={`step-label ${i === current ? 'active' : ''}`}>{label}</span>
                    </div>
                    {i < STEP_LABELS.length - 1 && (
                        <div key={`line-${i}`} className={`step-line ${i < current ? 'done' : ''}`} />
                    )}
                </>
            ))}
        </div>
    )
}

function ServiceCard({ service, selected, onSelect }) {
    const CATEGORY_ICONS = {
        haircut: '✂️', beard: '🪒', coloring: '🎨', styling: '💈',
        treatment: '✨', combo: '⭐', default: '💈'
    }
    return (
        <div className={`booking-card ${selected ? 'selected' : ''}`} onClick={() => onSelect(service)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <span style={{ fontSize: '1.5rem' }}>{CATEGORY_ICONS[service.category] || CATEGORY_ICONS.default}</span>
                    <h4 style={{ fontWeight: 900, fontSize: '14px', marginTop: '0.5rem' }}>{service.name}</h4>
                    <p style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '2px' }}>{service.duration || service.duration_minutes} min</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '1.25rem', fontWeight: 900, color: 'var(--gold)' }}>${service.price}</p>
                    {selected && <span style={{ fontSize: '9px', color: '#4ade80', fontWeight: 900 }}>✓ SELECCIONADO</span>}
                </div>
            </div>
            {service.description && (
                <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '0.75rem', lineHeight: 1.5 }}>{service.description}</p>
            )}
        </div>
    )
}

function BarberCard({ barber, selected, onSelect }) {
    return (
        <div className={`booking-card ${selected ? 'selected' : ''}`} onClick={() => onSelect(barber)} style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div style={{ width: '52px', height: '52px', borderRadius: '50%', background: 'rgba(212,175,55,0.1)', border: '2px solid rgba(212,175,55,0.2)', display: 'grid', placeItems: 'center', flexShrink: 0, overflow: 'hidden' }}>
                {barber.avatar ? (
                    <img src={barber.avatar} alt={barber.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                    <span style={{ fontSize: '1.25rem', fontWeight: 900, color: 'var(--gold)' }}>{(barber.name || 'B')[0]}</span>
                )}
            </div>
            <div style={{ flex: 1 }}>
                <h4 style={{ fontWeight: 900, fontSize: '14px' }}>{barber.name}</h4>
                <p style={{ fontSize: '10px', color: 'var(--gold)', fontWeight: 800, textTransform: 'uppercase' }}>{barber.specialization || 'Barbero'}</p>
                {barber.rating && (
                    <p style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '2px' }}>★ {barber.rating.toFixed(1)} · {barber.total_reviews || 0} reseñas</p>
                )}
            </div>
            {selected && (
                <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: 'var(--gold)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
                    <span style={{ color: '#000', fontSize: '11px', fontWeight: 900 }}>✓</span>
                </div>
            )}
        </div>
    )
}

function BookingSummary({ service, barber, date, time }) {
    if (!service && !barber) return null
    return (
        <div style={{ background: 'rgba(212,175,55,0.04)', border: '1px solid rgba(212,175,55,0.15)', borderRadius: '1rem', padding: '1.25rem' }}>
            <p style={{ fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--gold)', marginBottom: '0.75rem' }}>Resumen</p>
            {service && (
                <div className="receipt-line"><span style={{ color: 'var(--muted)' }}>Servicio</span><span style={{ fontWeight: 800 }}>{service.name}</span></div>
            )}
            {barber && (
                <div className="receipt-line"><span style={{ color: 'var(--muted)' }}>Maestro</span><span style={{ fontWeight: 800 }}>{barber.name}</span></div>
            )}
            {date && (
                <div className="receipt-line"><span style={{ color: 'var(--muted)' }}>Fecha</span><span style={{ fontWeight: 800 }}>{new Date(date + 'T12:00').toLocaleDateString('es-MX', { weekday: 'short', day: 'numeric', month: 'long' })}</span></div>
            )}
            {time && (
                <div className="receipt-line"><span style={{ color: 'var(--muted)' }}>Hora</span><span style={{ fontWeight: 800 }}>{time}</span></div>
            )}
            {service && (
                <div className="receipt-line" style={{ borderTop: '1px solid var(--line)', marginTop: '0.5rem', paddingTop: '0.75rem' }}>
                    <span>Total</span>
                    <span style={{ color: 'var(--gold)', fontSize: '16px' }}>${service.price}</span>
                </div>
            )}
        </div>
    )
}

export default function ClientBooking() {
    const [step, setStep] = useState(0)
    const [barbers, setBarbers] = useState([])
    const [services, setServices] = useState([])
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)

    const [selectedService, setSelectedService] = useState(null)
    const [selectedBarber, setSelectedBarber] = useState(null)
    const [selectedDate, setSelectedDate] = useState('')
    const [selectedTime, setSelectedTime] = useState('')
    const [notes, setNotes] = useState('')
    const [paymentMethod, setPaymentMethod] = useState('cash')

    useEffect(() => {
        const load = async () => {
            const stored = getStoredUser()
            if (!stored || stored.role !== 'client') { navigate('/login'); return }
            try {
                const [b, s] = await Promise.all([
                    apiFetch('/barbers').then(r => r.json()),
                    apiFetch('/services').then(r => r.json())
                ])
                setBarbers(b.data?.barbers || b.data || [])
                setServices(s.data?.services || s.data || [])
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [])

    const next = () => setStep(s => Math.min(s + 1, 3))
    const prev = () => setStep(s => Math.max(s - 1, 0))

    const canNext = () => {
        if (step === 0) return !!selectedService
        if (step === 1) return !!selectedBarber
        if (step === 2) return !!(selectedDate && selectedTime)
        return true
    }

    const confirmBooking = async (cardData) => {
        setSubmitting(true)
        try {
            const res = await apiFetch('/appointments', {
                method: 'POST',
                body: JSON.stringify({
                    barber_id: selectedBarber.id,
                    service_id: selectedService.id,
                    appointment_date: selectedDate,
                    start_time: selectedTime,
                    notes,
                })
            })
            if (!res.ok) {
                const data = await res.json()
                toast.error(data.detail || 'No se pudo agendar la cita')
                return
            }

            if (paymentMethod === 'stripe' && cardData) {
                await apiFetch('/payments/stripe/intent', {
                    method: 'POST',
                    body: JSON.stringify({
                        amount: selectedService.price,
                        method: 'credit_card',
                        card_last4: cardData.number.replace(/\s/g, '').slice(-4),
                    })
                })
            }

            toast.success('¡Cita confirmada con éxito!')
            setTimeout(() => navigate('/dashboard/client/history'), 1800)
        } finally {
            setSubmitting(false)
        }
    }

    const today = new Date().toISOString().split('T')[0]

    return (
        <div className="space-y-8 animate-fade-in">
            <div>
                <h2 className="ui-profile-title">Reserva <span className="text-gold">Premium</span></h2>
                <p className="ui-profile-subtitle">Tu ritual de excelencia comienza aquí</p>
            </div>

            <StepIndicator current={step} />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2">

                    {/* Step 0: Service */}
                    {step === 0 && (
                        <div className="space-y-4 animate-fade-in">
                            <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--gold)' }}>Elige tu Servicio</h3>
                            {loading ? (
                                [...Array(3)].map((_, i) => <div key={i} className="skeleton" style={{ height: '90px' }} />)
                            ) : (
                                <div className="space-y-3">
                                    {services.filter(s => s.is_active !== false).map(s => (
                                        <ServiceCard key={s.id} service={s} selected={selectedService?.id === s.id} onSelect={setSelectedService} />
                                    ))}
                                    {services.length === 0 && (
                                        <p style={{ color: 'var(--muted)', textAlign: 'center', padding: '2rem' }}>Sin servicios disponibles</p>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Step 1: Barber */}
                    {step === 1 && (
                        <div className="space-y-4 animate-fade-in">
                            <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--gold)' }}>Elige tu Maestro</h3>
                            <div className={`booking-card ${!selectedBarber ? 'selected' : ''}`} onClick={() => setSelectedBarber(null)} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                <div style={{ width: '52px', height: '52px', borderRadius: '50%', background: 'rgba(212,175,55,0.1)', border: '2px solid rgba(212,175,55,0.2)', display: 'grid', placeItems: 'center' }}>
                                    <span style={{ fontSize: '1.25rem' }}>🎲</span>
                                </div>
                                <div>
                                    <h4 style={{ fontWeight: 900, fontSize: '14px' }}>Cualquier Profesional</h4>
                                    <p style={{ fontSize: '10px', color: 'var(--muted)' }}>Se asignará el maestro disponible</p>
                                </div>
                                {!selectedBarber && (
                                    <div style={{ marginLeft: 'auto', width: '22px', height: '22px', borderRadius: '50%', background: 'var(--gold)', display: 'grid', placeItems: 'center' }}>
                                        <span style={{ color: '#000', fontSize: '11px', fontWeight: 900 }}>✓</span>
                                    </div>
                                )}
                            </div>
                            {loading ? (
                                [...Array(2)].map((_, i) => <div key={i} className="skeleton" style={{ height: '80px' }} />)
                            ) : (
                                barbers.map(b => (
                                    <BarberCard key={b.id} barber={b} selected={selectedBarber?.id === b.id} onSelect={setSelectedBarber} />
                                ))
                            )}
                        </div>
                    )}

                    {/* Step 2: Date & Time */}
                    {step === 2 && (
                        <div className="space-y-6 animate-fade-in">
                            <div className="group">
                                <label className="ui-kpi-label">Fecha de Visita</label>
                                <input
                                    type="date"
                                    className="ui-input"
                                    style={{ marginTop: '0.5rem', fontSize: '1rem' }}
                                    value={selectedDate}
                                    onChange={e => setSelectedDate(e.target.value)}
                                    min={today}
                                />
                            </div>
                            <div>
                                <label className="ui-kpi-label" style={{ display: 'block', marginBottom: '0.75rem' }}>Horario Disponible</label>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(70px, 1fr))', gap: '0.5rem' }}>
                                    {TIMES.map(t => (
                                        <button
                                            key={t}
                                            type="button"
                                            className={`time-slot available ${selectedTime === t ? 'selected' : ''}`}
                                            onClick={() => setSelectedTime(t)}
                                        >
                                            {t}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="group">
                                <label className="ui-kpi-label">Notas para el Maestro (opcional)</label>
                                <textarea
                                    className="ui-input"
                                    style={{ minHeight: '80px', resize: 'none', marginTop: '0.5rem' }}
                                    value={notes}
                                    onChange={e => setNotes(e.target.value)}
                                    placeholder="Preferencias, estilo o indicaciones especiales..."
                                />
                            </div>
                        </div>
                    )}

                    {/* Step 3: Payment */}
                    {step === 3 && (
                        <div className="space-y-6 animate-fade-in">
                            <h3 style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--gold)' }}>Método de Pago</h3>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                                {[
                                    { key: 'cash', label: 'Pagar en Tienda', icon: '💵', desc: 'Al llegar a la cita' },
                                    { key: 'stripe', label: 'Tarjeta Online', icon: '💳', desc: 'Pago seguro con Stripe' },
                                ].map(m => (
                                    <button
                                        key={m.key}
                                        type="button"
                                        className={`method-btn ${paymentMethod === m.key ? 'selected' : ''}`}
                                        style={{ padding: '1.25rem', flexDirection: 'column', gap: '0.5rem', height: 'auto' }}
                                        onClick={() => setPaymentMethod(m.key)}
                                    >
                                        <span style={{ fontSize: '1.75rem' }}>{m.icon}</span>
                                        <span style={{ fontSize: '10px', fontWeight: 900 }}>{m.label}</span>
                                        <span style={{ fontSize: '9px', color: 'var(--muted)', textTransform: 'none', letterSpacing: 0, fontWeight: 400 }}>{m.desc}</span>
                                    </button>
                                ))}
                            </div>

                            {paymentMethod === 'cash' && (
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem', padding: '2rem', textAlign: 'center' }}>
                                    <div style={{ fontSize: '3rem' }}>🏪</div>
                                    <div>
                                        <p style={{ fontWeight: 900, fontSize: '16px' }}>Pago en Tienda</p>
                                        <p style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '0.5rem', lineHeight: 1.6 }}>
                                            Tu cita quedará reservada. Realiza el pago al llegar al local.<br />
                                            Por favor llega 5 minutos antes de tu cita.
                                        </p>
                                    </div>
                                    <button
                                        className="ui-btn-gold"
                                        style={{ width: '100%', maxWidth: '300px', padding: '1.25rem' }}
                                        disabled={submitting}
                                        onClick={() => confirmBooking(null)}
                                    >
                                        {submitting ? (
                                            <span style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', justifyContent: 'center' }}>
                                                <span className="spinner" style={{ width: '14px', height: '14px' }} />
                                                Confirmando...
                                            </span>
                                        ) : 'Confirmar Reserva →'}
                                    </button>
                                </div>
                            )}

                            {paymentMethod === 'stripe' && (
                                <StripeCardForm
                                    amount={selectedService?.price}
                                    loading={submitting}
                                    onSubmit={(cardData) => confirmBooking(cardData)}
                                />
                            )}
                        </div>
                    )}

                    {/* Navigation */}
                    {step < 3 && (
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
                            <button
                                type="button"
                                className="ui-btn"
                                style={{ background: 'transparent', visibility: step === 0 ? 'hidden' : 'visible' }}
                                onClick={prev}
                            >
                                ← Anterior
                            </button>
                            <button
                                type="button"
                                className="ui-btn-gold"
                                onClick={next}
                                disabled={!canNext()}
                                style={{ opacity: canNext() ? 1 : 0.4 }}
                            >
                                {step === 2 ? 'Ir a Pago →' : 'Continuar →'}
                            </button>
                        </div>
                    )}
                    {step === 3 && paymentMethod !== 'stripe' && step !== 0 && (
                        <div style={{ marginTop: '1rem' }}>
                            <button type="button" className="ui-btn" style={{ background: 'transparent' }} onClick={prev}>← Volver</button>
                        </div>
                    )}
                </div>

                {/* Sidebar summary */}
                <aside className="space-y-5">
                    <BookingSummary
                        service={selectedService}
                        barber={selectedBarber}
                        date={selectedDate}
                        time={selectedTime}
                    />
                    <div style={{ background: 'rgba(212,175,55,0.04)', border: '1px solid rgba(212,175,55,0.12)', borderRadius: '1rem', padding: '1.25rem' }}>
                        <h4 style={{ fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.16em', color: 'var(--gold)', marginBottom: '0.75rem' }}>
                            Protocolo Premium
                        </h4>
                        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                            {[
                                'Llega 5 minutos antes de tu cita',
                                'Incluye consulta de imagen personalizada',
                                'Cancelaciones hasta 12h de anticipación',
                                'Garantía de satisfacción total',
                            ].map((item, i) => (
                                <li key={i} style={{ fontSize: '11px', color: 'var(--muted)', display: 'flex', gap: '0.5rem', lineHeight: 1.5 }}>
                                    <span style={{ color: 'var(--gold)', flexShrink: 0 }}>✦</span>
                                    {item}
                                </li>
                            ))}
                        </ul>
                    </div>
                </aside>
            </div>
        </div>
    )
}
