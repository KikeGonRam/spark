import Navbar from '../components/Navbar'
import { services, barbers } from '../constants'
import { navigate } from '../hooks/useNavigation'

export default function HomeScreen() {
  return (
    <div className="site">
      <Navbar />
      
      {/* Hero Section */}
      <header className="hero" id="inicio">
        <div className="hero-bg" />
        <div className="hero-overlay" />
        
        <div className="hero-content">
          <div className="animate-bounce" style={{ marginBottom: '2rem' }}>
            <span className="ui-badge">Tradición & Vanguardia</span>
          </div>
          <h1>
            LA <span className="text-gradient-gold">EXCELENCIA</span> <br /> 
            <span className="ui-title-serif" style={{ fontSize: '0.6em', textTransform: 'none', display: 'block', marginTop: '-10px' }}>
              en cada detalle
            </span>
          </h1>
          <p>
            Elevamos el concepto de barbería a un estudio de arte. Un espacio diseñado para el hombre que exige perfección y confort.
          </p>
          <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/register" onClick={(e) => { e.preventDefault(); navigate('/register') }} className="ui-btn" style={{ minWidth: '250px', padding: '1.25rem' }}>
              Agendar Cita Premium
            </a>
            <a href="#servicios" className="ui-btn-secondary" style={{ minWidth: '250px', padding: '1.25rem' }}>
              Nuestros Servicios
            </a>
          </div>
        </div>
      </header>

      {/* Services Section */}
      <section id="servicios" className="section dark">
        <div className="container">
          <div className="section-header">
            <p>Maestría artesanal para tu estilo personal</p>
            <h2>Servicios <span className="text-gradient-gold">Signature</span></h2>
            <div style={{ height: '4px', width: '96px', background: 'var(--gold)', margin: '1.5rem auto', borderRadius: '99px' }}></div>
          </div>

          <div className="grid services-grid">
            {services.map((service, index) => (
              <article key={index} className="ui-card-premium">
                <div className="service-icon">
                   <svg style={{ width: '1.75rem', height: '1.75rem' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758L5 19m0-14l4.121 4.121" />
                    </svg>
                </div>
                <h3 style={{ fontSize: '1.5rem', fontWeight: 900, textTransform: 'uppercase', marginBottom: '1rem' }}>{service.title}</h3>
                <p style={{ color: 'var(--muted)', fontSize: '0.875rem', marginBottom: '2rem' }}>{service.desc || 'Una experiencia diseñada para resaltar tu mejor versión con técnica clásica.'}</p>
                <div className="service-footer">
                  <span style={{ fontSize: '1.25rem', fontWeight: 900 }}>{service.price}</span>
                  <span className="ui-badge" style={{ fontSize: '10px', padding: '4px 12px' }}>{service.time}</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section id="equipo" className="section">
        <div className="container">
          <div className="section-header" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '3rem', textAlign: 'left' }}>
                <div>
                    <p>Arquitectos de la imagen masculina</p>
                    <h2 style={{ fontSize: '2.25rem' }}>Los <span className="text-gradient-gold">Maestros</span></h2>
                </div>
                <a href="/register" onClick={(e) => { e.preventDefault(); navigate('/register') }} style={{ fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', color: 'var(--gold)', letterSpacing: '0.2em' }}>
                    Ver todo el equipo &rarr;
                </a>
            </div>
          </div>

          <div className="grid team-grid">
            {barbers.map((barber, index) => (
              <a key={index} href="/register" onClick={(e) => { e.preventDefault(); navigate('/register') }} className="barber-card">
                <div className="barber-photo">
                   <div style={{ width: '100%', height: '100%', background: '#222', display: 'grid', placeItems: 'center', fontSize: '3rem', fontWeight: 900, color: 'rgba(255,255,255,0.05)' }}>
                     {barber.initials}
                   </div>
                   <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, black, transparent)', opacity: 0.8 }}></div>
                   <div style={{ position: 'absolute', bottom: '1.5rem', left: '1.5rem' }}>
                        <h4 style={{ fontSize: '1.125rem', fontWeight: 900, textTransform: 'uppercase' }}>{barber.name}</h4>
                        <p style={{ fontSize: '9px', fontWeight: 700, color: 'var(--gold)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{barber.role}</p>
                   </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="section dark" style={{ background: 'linear-gradient(to bottom, #0a0a0a, #0d0d0d)' }}>
        <div className="container">
            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', alignItems: 'center', gap: '5rem' }}>
                <div>
                    <h2 style={{ fontSize: '2.25rem', fontWeight: 900, textTransform: 'uppercase', lineHeight: 1.1 }}>
                        Lo que dicen <br /> nuestros <span className="text-gradient-gold">Caballeros</span>
                    </h2>
                    <p style={{ marginTop: '1.5rem', color: 'var(--muted)', fontSize: '1.125rem' }}>
                        Nuestra reputación se ha forjado con precisión y satisfacción. Únete a la comunidad BarberPro.
                    </p>
                    <div style={{ marginTop: '2.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <div style={{ display: 'flex', marginLeft: '0.75rem' }}>
                            {[1,2,3,4].map(i => (
                                <div key={i} style={{ width: '3rem', height: '3rem', borderRadius: '9999px', border: '4px solid #0a0a0a', background: '#222', marginLeft: '-0.75rem' }}></div>
                            ))}
                        </div>
                        <div>
                            <p style={{ fontSize: '0.875rem', fontWeight: 900 }}>500+ Reseñas</p>
                            <div style={{ color: 'var(--gold)', fontSize: '0.75rem' }}>★★★★★</div>
                        </div>
                    </div>
                </div>
                <div style={{ display: 'grid', gap: '1.5rem' }}>
                    <div className="ui-card-premium" style={{ padding: '2rem', background: 'rgba(212,175,55,0.05)', borderColor: 'rgba(212,175,55,0.2)' }}>
                        <p style={{ fontSize: '1.125rem', fontStyle: 'italic', color: '#fff' }}>"La atención al detalle es increíble. No es solo un corte, es un ritual de relajación. Totalmente recomendado."</p>
                        <p style={{ marginTop: '1.5rem', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', color: 'var(--gold)' }}>— Ricardo Arjona, Cliente VIP</p>
                    </div>
                    <div className="ui-card-premium" style={{ padding: '2rem' }}>
                        <p style={{ fontSize: '1.125rem', fontStyle: 'italic', color: '#fff' }}>"El sistema de reservas es súper rápido. Llego y mi barbero ya me está esperando. Eficiencia y lujo en un solo lugar."</p>
                        <p style={{ marginTop: '1.5rem', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', color: 'var(--muted)' }}>— Julian Casas, Emprendedor</p>
                    </div>
                </div>
            </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ padding: '5rem 0', textAlign: 'center', borderTop: '1px solid rgba(255,255,255,0.05)', background: '#0a0a0a' }}>
         <div className="nav-brand" style={{ justifyContent: 'center', marginBottom: '2rem' }}>
            <div className="nav-mark">
                <svg style={{ width: '1.5rem', height: '1.5rem' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
            </div>
            <span style={{ fontWeight: 900, textTransform: 'uppercase', marginLeft: '0.75rem', fontSize: '1.5rem' }}>Barber<span style={{ color: 'var(--gold)' }}>Pro</span></span>
         </div>
         <p style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.2em', color: 'var(--muted)' }}>
            &copy; 2026 BarberPro Studio. La excelencia en cada detalle.
         </p>
      </footer>
    </div>
  )
}
