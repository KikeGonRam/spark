import { useState, useEffect, useRef } from 'react'
import { apiFetch } from '../hooks/useNavigation'

export default function AIChatbot() {
    const [isOpen, setIsOpen] = useState(false)
    const [messages, setMessages] = useState([
        { role: 'assistant', content: '¡Hola! Soy tu Asistente de Estilo BarberPro. ¿En qué puedo ayudarte hoy?' }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const scrollRef = useRef(null)

    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }, [messages])

    const handleSendMessage = async (e) => {
        e.preventDefault()
        if (!input.trim() || loading) return

        const userMessage = { role: 'user', content: input }
        setMessages(prev => [...prev, userMessage])
        setInput('')
        setLoading(true)

        try {
            const res = await apiFetch('/chatbot/chat', {
                method: 'POST',
                body: JSON.stringify({ message: userMessage.content })
            })
            
            if (res.status === 429) {
                setMessages(prev => [...prev, { role: 'assistant', content: 'Nuestra IA está tomando un breve descanso por alta demanda. Por favor, intenta de nuevo en unos segundos.' }])
            } else if (res.ok) {
                const data = await res.json()
                setMessages(prev => [...prev, { role: 'assistant', content: data.message }])
            } else {
                setMessages(prev => [...prev, { role: 'assistant', content: 'Lo siento, no pude procesar tu solicitud en este momento.' }])
            }
        } catch (error) {
            setMessages(prev => [...prev, { role: 'assistant', content: 'Error de conexión. Verifica tu internet.' }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <>
            <button onClick={() => setIsOpen(!isOpen)} className="animate-bounce" style={{
                position: 'fixed', bottom: '30px', right: '30px', width: '60px', height: '60px', borderRadius: '50%',
                background: 'var(--gold)', border: 'none', boxShadow: '0 10px 25px rgba(212,175,55,0.3)',
                cursor: 'pointer', zIndex: 9999, display: 'grid', placeItems: 'center'
            }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth="2.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </button>

            {isOpen && (
                <div className="glass animate-slide-up" style={{
                    position: 'fixed', bottom: '100px', right: '30px', width: '350px', height: '450px', borderRadius: '20px',
                    display: 'flex', flexDirection: 'column', zIndex: 9998, boxShadow: '0 20px 50px rgba(0,0,0,0.5)', border: '1px solid rgba(212,175,55,0.2)'
                }}>
                    <div style={{ padding: '16px', background: 'rgba(212,175,55,0.1)', borderBottom: '1px solid rgba(212,175,55,0.1)' }}>
                        <p style={{ fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--gold)' }}>BarberPro AI Assistant</p>
                    </div>

                    <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {messages.map((m, i) => (
                            <div key={i} style={{ 
                                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                                maxWidth: '80%', padding: '10px 14px', borderRadius: '12px', fontSize: '12px',
                                background: m.role === 'user' ? 'var(--gold)' : '#1a1a1a',
                                color: m.role === 'user' ? '#000' : '#fff',
                                wordBreak: 'break-word'
                            }}>
                                {m.content}
                            </div>
                        ))}
                    </div>

                    <form onSubmit={handleSendMessage} style={{ padding: '16px', borderTop: '1px solid #1a1a1a' }}>
                        <input className="ui-input" style={{ fontSize: '12px' }} placeholder="Escribe algo..." value={input} onChange={e => setInput(e.target.value)} />
                    </form>
                </div>
            )}
        </>
    )
}
