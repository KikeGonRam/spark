import { useState } from 'react'
import Navbar from '../components/Navbar'
import { dashboardLinks } from '../constants'
import { navigate, apiFetch } from '../hooks/useNavigation'

export default function AuthScreen({ title, titleGold, subtitle, submit, children }) {
  const [status, setStatus] = useState('')
  const isLogin = submit === 'Iniciar Sesión'
  const redirectTo = (role) => navigate(role === 'admin' ? '/dashboard/admin' : role === 'barber' ? '/dashboard/barber' : '/dashboard/client')
  
  const onSubmit = async (e) => {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const payload = Object.fromEntries(form.entries())
    try {
      const res = await apiFetch(isLogin ? '/auth/login' : '/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'No se pudo completar la operación')
      const token = data.token || data.access_token || data.refresh_token
      if (token) localStorage.setItem('barberpro_token', token)
      const user = data.user || await apiFetch('/auth/me').then((r) => r.ok ? r.json() : null).then((r) => r?.data || null).catch(() => null)
      if (user) localStorage.setItem('barberpro_user', JSON.stringify(user))
      const role = user?.role || payload.role || 'client'
      setStatus(isLogin ? 'Sesión iniciada' : 'Registro exitoso')
      redirectTo(role)
    } catch (err) {
      setStatus(err.message)
    }
  }

  return (
    <div className="auth-page">
      <Navbar />
      <section className="auth-section">
        <div className="container">
            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', alignItems: 'center', gap: '4rem' }}>
                
                {/* Hero Side */}
                <div className="auth-hero" style={{ paddingRight: '2rem' }}>
                    <span className="ui-badge" style={{ marginBottom: '2rem' }}>BarberPro Studio</span>
                    <h1 style={{ fontSize: '4rem', fontWeight: 900, textTransform: 'uppercase', lineHeight: 1 }}>
                        {title} <br />
                        <span className="ui-title-serif" style={{ textTransform: 'lowercase', fontSize: '0.8em' }}>{titleGold}</span>
                    </h1>
                    <p style={{ marginTop: '2rem', color: 'var(--muted)', fontSize: '1.125rem' }}>{subtitle}</p>
                    <div style={{ marginTop: '3rem', display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
                        {dashboardLinks.map((d) => (
                            <a key={d.path} href={d.path} onClick={(e) => { e.preventDefault(); navigate(d.path) }} style={{ fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', color: 'var(--gold)', letterSpacing: '0.1em' }}>
                                {d.label}
                            </a>
                        ))}
                    </div>
                </div>

                {/* Card Side */}
                <article className="auth-card">
                    <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
                        <h2 style={{ textTransform: 'uppercase', fontWeight: 900, fontSize: '1.5rem', letterSpacing: '0.05em' }}>{submit}</h2>
                        <p style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', letterSpacing: '0.2em', marginTop: '0.5rem' }}>Acceso Premium Garantizado</p>
                    </div>

                    <form className="auth-form" onSubmit={onSubmit}>
                    {children}
                    {status ? <p style={{ color: 'var(--gold)', fontSize: '0.75rem', textAlign: 'center', marginBottom: '1rem', fontWeight: 700, textTransform: 'uppercase' }}>{status}</p> : null}
                    <button type="submit" className="ui-btn" style={{ width: '100%', padding: '1.25rem' }}>
                        {submit} <span style={{ marginLeft: '0.5rem', opacity: 0.5 }}>&rarr;</span>
                    </button>
                    </form>

                    <div style={{ textAlign: 'center', marginTop: '2.5rem' }}>
                        <p style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', letterSpacing: '0.1em' }}>
                            {isLogin ? "¿Aún no tienes cuenta?" : "¿Ya tienes cuenta?"} 
                            <a href={isLogin ? "/register" : "/login"} onClick={(e) => { e.preventDefault(); navigate(isLogin ? "/register" : "/login") }} style={{ color: 'var(--gold)', marginLeft: '0.5rem', textDecoration: 'underline' }}>
                                {isLogin ? "Regístrate ahora" : "Inicia sesión aquí"}
                            </a>
                        </p>
                    </div>
                </article>

            </div>
        </div>
      </section>
    </div>
  )
}
