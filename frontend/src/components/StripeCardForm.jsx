import { useState } from 'react'

const CARD_TYPES = {
    visa:       { pattern: /^4/,            label: 'VISA',       color: '#1a1f71' },
    mastercard: { pattern: /^5[1-5]/,       label: 'MASTERCARD', color: '#eb001b' },
    amex:       { pattern: /^3[47]/,        label: 'AMEX',       color: '#007bc1' },
    discover:   { pattern: /^6(?:011|5)/,   label: 'DISCOVER',   color: '#ff6600' },
}

function detectCard(num) {
    const clean = num.replace(/\s/g, '')
    for (const [type, info] of Object.entries(CARD_TYPES)) {
        if (info.pattern.test(clean)) return { type, ...info }
    }
    return null
}

function formatCardNumber(val) {
    const clean = val.replace(/\D/g, '').slice(0, 16)
    return clean.match(/.{1,4}/g)?.join(' ') || clean
}

function formatExpiry(val) {
    const clean = val.replace(/\D/g, '').slice(0, 4)
    if (clean.length >= 3) return clean.slice(0, 2) + '/' + clean.slice(2)
    return clean
}

function validateCard(data) {
    const errors = {}
    const num = data.number.replace(/\s/g, '')
    if (num.length < 13) errors.number = 'Número inválido'
    const [mm, yy] = data.expiry.split('/')
    if (!mm || !yy || parseInt(mm) > 12 || parseInt(mm) < 1) errors.expiry = 'Fecha inválida'
    if (yy) {
        const expYear = 2000 + parseInt(yy)
        const expMonth = parseInt(mm)
        const now = new Date()
        if (expYear < now.getFullYear() || (expYear === now.getFullYear() && expMonth < now.getMonth() + 1)) {
            errors.expiry = 'Tarjeta vencida'
        }
    }
    if (data.cvv.length < 3) errors.cvv = 'CVV inválido'
    if (data.name.trim().length < 2) errors.name = 'Nombre requerido'
    return errors
}

export default function StripeCardForm({ onSubmit, amount, loading }) {
    const [card, setCard] = useState({ number: '', expiry: '', cvv: '', name: '' })
    const [errors, setErrors] = useState({})
    const [flipped, setFlipped] = useState(false)

    const cardType = detectCard(card.number)
    const maskedNum = card.number || '•••• •••• •••• ••••'
    const maskedExp = card.expiry || 'MM/AA'
    const maskedName = card.name.toUpperCase() || 'NOMBRE APELLIDO'

    const handleChange = (field, raw) => {
        let val = raw
        if (field === 'number') val = formatCardNumber(raw)
        if (field === 'expiry') val = formatExpiry(raw)
        if (field === 'cvv') val = raw.replace(/\D/g, '').slice(0, 4)
        setCard(prev => ({ ...prev, [field]: val }))
        if (errors[field]) setErrors(prev => ({ ...prev, [field]: undefined }))
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        const errs = validateCard(card)
        if (Object.keys(errs).length) { setErrors(errs); return }
        onSubmit?.({ ...card, cardType: cardType?.type || 'unknown' })
    }

    return (
        <div className="space-y-6">
            {/* Card visual */}
            <div className="card-visual" style={{ maxWidth: '340px', margin: '0 auto' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div className="card-chip" />
                    {cardType ? (
                        <span style={{ fontSize: '13px', fontWeight: 900, color: 'rgba(255,255,255,0.7)', letterSpacing: '0.05em' }}>
                            {cardType.label}
                        </span>
                    ) : (
                        <svg width="40" height="24" viewBox="0 0 40 24" fill="none">
                            <rect x="0" y="0" width="40" height="24" rx="4" fill="rgba(255,255,255,0.06)" />
                            <circle cx="14" cy="12" r="8" fill="rgba(255,255,255,0.12)" />
                            <circle cx="26" cy="12" r="8" fill="rgba(255,255,255,0.08)" />
                        </svg>
                    )}
                </div>
                <div className="card-number-display">{maskedNum}</div>
                <div className="card-info-row">
                    <div>
                        <div className="card-label-sm">Titular</div>
                        <div className="card-value-sm" style={{ fontSize: '11px' }}>{maskedName}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <div className="card-label-sm">Vence</div>
                        <div className="card-value-sm">{maskedExp}</div>
                    </div>
                    {amount && (
                        <div style={{ textAlign: 'right' }}>
                            <div className="card-label-sm">Total</div>
                            <div className="card-value-sm" style={{ color: 'var(--gold)' }}>${amount}</div>
                        </div>
                    )}
                </div>
            </div>

            {/* Form fields */}
            <form onSubmit={handleSubmit} className="space-y-4">
                <div className="group">
                    <label className="ui-kpi-label">Nombre en la tarjeta</label>
                    <input
                        className={`stripe-card-field ${errors.name ? 'error' : card.name.length > 2 ? 'valid' : ''}`}
                        style={{ fontFamily: 'inherit', letterSpacing: 'normal' }}
                        placeholder="Como aparece en la tarjeta"
                        value={card.name}
                        onChange={e => handleChange('name', e.target.value)}
                        autoComplete="cc-name"
                    />
                    {errors.name && <p style={{ color: '#f87171', fontSize: '10px', marginTop: '4px' }}>{errors.name}</p>}
                </div>

                <div className="group">
                    <label className="ui-kpi-label">Número de tarjeta</label>
                    <input
                        className={`stripe-card-field ${errors.number ? 'error' : card.number.replace(/\s/g,'').length === 16 ? 'valid' : ''}`}
                        placeholder="1234 5678 9012 3456"
                        value={card.number}
                        onChange={e => handleChange('number', e.target.value)}
                        inputMode="numeric"
                        autoComplete="cc-number"
                        maxLength={19}
                    />
                    {errors.number && <p style={{ color: '#f87171', fontSize: '10px', marginTop: '4px' }}>{errors.number}</p>}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className="group">
                        <label className="ui-kpi-label">Fecha de vencimiento</label>
                        <input
                            className={`stripe-card-field ${errors.expiry ? 'error' : card.expiry.length === 5 ? 'valid' : ''}`}
                            placeholder="MM/AA"
                            value={card.expiry}
                            onChange={e => handleChange('expiry', e.target.value)}
                            inputMode="numeric"
                            autoComplete="cc-exp"
                            maxLength={5}
                        />
                        {errors.expiry && <p style={{ color: '#f87171', fontSize: '10px', marginTop: '4px' }}>{errors.expiry}</p>}
                    </div>
                    <div className="group">
                        <label className="ui-kpi-label">CVV / CVC</label>
                        <input
                            className={`stripe-card-field ${errors.cvv ? 'error' : card.cvv.length >= 3 ? 'valid' : ''}`}
                            placeholder="•••"
                            value={card.cvv}
                            onChange={e => handleChange('cvv', e.target.value)}
                            onFocus={() => setFlipped(true)}
                            onBlur={() => setFlipped(false)}
                            inputMode="numeric"
                            autoComplete="cc-csc"
                            maxLength={4}
                            type="password"
                        />
                        {errors.cvv && <p style={{ color: '#f87171', fontSize: '10px', marginTop: '4px' }}>{errors.cvv}</p>}
                    </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1rem', background: 'rgba(74,222,128,0.04)', border: '1px solid rgba(74,222,128,0.12)', borderRadius: '0.75rem' }}>
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: '#4ade80', flexShrink: 0 }}>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    <span style={{ fontSize: '10px', color: '#4ade80', fontWeight: 700 }}>Pago seguro cifrado con SSL · Powered by Stripe</span>
                </div>

                <button
                    type="submit"
                    className="ui-btn-gold"
                    style={{ width: '100%', padding: '1.1rem', fontSize: '11px' }}
                    disabled={loading}
                >
                    {loading ? (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', justifyContent: 'center' }}>
                            <span className="spinner" style={{ width: '14px', height: '14px' }} />
                            Procesando pago...
                        </span>
                    ) : (
                        `Pagar ${amount ? `$${amount}` : ''} →`
                    )}
                </button>
            </form>
        </div>
    )
}
