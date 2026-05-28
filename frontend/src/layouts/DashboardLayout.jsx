import { navigate } from '../hooks/useNavigation'

const I = {
  Overview: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>,
  Calendar: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>,
  Scissors: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758L5 19m0-14l4.121 4.121" /></svg>,
  Users: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
  UserSingle: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>,
  Box: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>,
  Money: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  Chart: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
  Gear: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
  Log: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>,
  AI: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>,
  Clock: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  Portfolio: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>,
  Star: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>,
  Bell: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>,
  Plus: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M12 4v16m8-8H4" /></svg>,
  History: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  Logout: () => <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>,
}

export default function DashboardLayout({ children, role, subview }) {
    // Normalize role: frontend may receive human labels ('Administrativo') or raw codes ('admin')
    const r = (role || '').toString().toLowerCase()
    const isAdmin = r.includes('admin') || r.includes('administr') || r === 'administrativo'
    const isBarber = r.includes('barber') || r.includes('profes') || r === 'profesional'
    const basePath = isAdmin ? '/dashboard/admin' : (isBarber ? '/dashboard/barber' : '/dashboard/client')

    const adminMenu = [
        { id: 'overview', label: 'Dashboard', path: basePath, icon: I.Overview },
        { id: 'appointments', label: 'Citas', path: `${basePath}/appointments`, icon: I.Calendar },
        { id: 'services', label: 'Servicios', path: `${basePath}/services`, icon: I.Scissors },
        { id: 'clients', label: 'Clientes', path: `${basePath}/clients`, icon: I.Users },
        { id: 'barbers', label: 'Barberos', path: `${basePath}/barbers`, icon: I.Star },
        { id: 'users', label: 'Usuarios', path: `${basePath}/users`, icon: I.UserSingle },
        { id: 'payments', label: 'Pagos', path: `${basePath}/payments`, icon: I.Money },
        { id: 'inventory', label: 'Inventario', path: `${basePath}/inventory`, icon: I.Box },
        { id: 'reports', label: 'Reportes', path: `${basePath}/reports`, icon: I.Chart },
        { id: 'predictions', label: 'Predicciones', path: `${basePath}/predictions`, icon: I.AI },
        { id: 'settings', label: 'Ajustes', path: `${basePath}/settings`, icon: I.Gear },
        { id: 'logs', label: 'Logs', path: `${basePath}/logs`, icon: I.Log },
    ]

    const barberMenu = [
        { id: 'overview', label: 'Mi Inicio', path: basePath, icon: I.Overview },
        { id: 'agenda', label: 'Mi Agenda', path: `${basePath}/agenda`, icon: I.Calendar },
        { id: 'schedule', label: 'Mi Horario', path: `${basePath}/schedule`, icon: I.Clock },
        { id: 'portfolio', label: 'Portafolio', path: `${basePath}/portfolio`, icon: I.Portfolio },
        { id: 'profile', label: 'Mi Perfil', path: `${basePath}/profile`, icon: I.UserSingle },
    ]

    const clientMenu = [
        { id: 'overview', label: 'Mi Club', path: basePath, icon: I.Overview },
        { id: 'booking', label: 'Reservar', path: `${basePath}/booking`, icon: I.Plus },
        { id: 'history', label: 'Mi Historial', path: `${basePath}/history`, icon: I.History },
        { id: 'notifications', label: 'Avisos', path: `${basePath}/notifications`, icon: I.Bell },
        { id: 'profile', label: 'Mi Perfil', path: `${basePath}/profile`, icon: I.UserSingle },
    ]

    const menuItems = isAdmin ? adminMenu : (isBarber ? barberMenu : clientMenu)
    const roleLabel = isAdmin ? 'Administrador' : isBarber ? 'Profesional' : 'Cliente'

    const handleLogout = () => {
        localStorage.removeItem('barberpro_token')
        localStorage.removeItem('barberpro_user')
        navigate('/login')
    }

    return (
        <div className="dashboard-container">
            <aside className="sidebar">
                <div className="sidebar-logo">
                    <div style={{ background: 'var(--gold)', color: '#000', width: '28px', height: '28px', borderRadius: '6px', display: 'grid', placeItems: 'center', fontWeight: 900, fontSize: '14px', flexShrink: 0 }}>B</div>
                    <span>Barber<span style={{ color: 'var(--gold)' }}>Pro</span></span>
                </div>

                <nav className="sidebar-nav">
                    <p style={{ fontSize: '8px', fontWeight: 900, color: '#333', textTransform: 'uppercase', letterSpacing: '0.2em', padding: '0 1.2rem 1rem' }}>
                        Panel {roleLabel}
                    </p>
                    {menuItems.map((item) => (
                        <a key={item.id} href={item.path} className={`sidebar-link ${subview === item.id ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); navigate(item.path) }}>
                            <item.icon />
                            <span>{item.label}</span>
                        </a>
                    ))}
                </nav>

                <div style={{ padding: '1rem', borderTop: '1px solid var(--line)' }}>
                    <button onClick={handleLogout} className="sidebar-link" style={{ width: '100%', background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--muted)' }}>
                        <I.Logout />
                        <span>Cerrar Sesión</span>
                    </button>
                </div>
            </aside>

            <main className="main-content">
                <div className="animate-fade-in">
                    {children}
                </div>
            </main>
        </div>
    )
}
