import { useMemo } from 'react'
import { usePathname, navigate, getStoredUser, decodeJwtPayload, getStoredToken } from '../hooks/useNavigation'

function NavLink({ to, children, active, className = "", onClick }) { 
  return (
    <a 
      href={to} 
      onClick={(e) => { e.preventDefault(); onClick ? onClick(e) : navigate(to) }} 
      className={`${active ? 'active' : ''} ${className}`}
    >
      {children}
    </a> 
  )
}

export default function Navbar() {
  const pathname = usePathname()
  const isDashboard = pathname.startsWith('/dashboard')
  const token = getStoredToken()
  const storedUser = getStoredUser()
  const jwtPayload = decodeJwtPayload(token)
  const role = storedUser?.role || jwtPayload?.role || null
  const isLogged = !!token
  const dashboardHref = useMemo(() => {
    if (role === 'admin') return '/dashboard/admin'
    if (role === 'barber') return '/dashboard/barber'
    return '/dashboard/client'
  }, [pathname, role])
  return (
    <nav className="nav">
      <div className="nav-brand">
        <div className="nav-mark">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <a href="/" onClick={(e) => { e.preventDefault(); navigate('/') }}>Barber<span>Pro</span></a>
      </div>
      <div className="nav-links">
        <NavLink to="/" active={pathname === '/'}>Inicio</NavLink>
        <a href="#servicios">Servicios</a>
        <a href="#equipo">Maestros</a>
        <a href="#contacto">Ubicación</a>
        <div className="nav-divider" />
        {isLogged ? (
          <NavLink to={dashboardHref} active={isDashboard} className="ui-btn nav-cta">Mi Panel</NavLink>
        ) : (
          <>
            <NavLink to="/login" active={pathname === '/login'}>Acceso</NavLink>
            <NavLink to="/register" active={pathname === '/register'} className="ui-btn nav-cta">Reservar</NavLink>
          </>
        )}
      </div>
    </nav>
  )
}
