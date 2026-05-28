import { usePathname, navigate, getStoredToken, decodeJwtPayload, getStoredUser } from './hooks/useNavigation'
import HomeScreen from './screens/HomeScreen'
import AuthScreen from './screens/AuthScreen'
import DashboardScreen from './screens/DashboardScreen'
import AIChatbot from './components/AIChatbot'
import ToastContainer from './components/ToastContainer'

export default function App() {
  const pathname = usePathname()
  const token = getStoredToken()
  const storedUser = getStoredUser()
  const jwtPayload = decodeJwtPayload(token)
  const role = storedUser?.role || jwtPayload?.role || null
  const dashboardPath = role === 'admin' ? '/dashboard/admin' : role === 'barber' ? '/dashboard/barber' : '/dashboard/client'

  if ((pathname === '/' || pathname === '/login' || pathname === '/register') && token) {
    navigate(dashboardPath)
    return null
  }

  if (pathname.startsWith('/dashboard') && !token) {
    navigate('/login')
    return null
  }

  // Auth Routes
  if (pathname === '/login') {
    return (
      <AuthScreen title="Bienvenido" titleGold="de nuevo" subtitle="Introduce tus credenciales para continuar" submit="Iniciar Sesión">
        <div className="group">
          <label>Correo Electrónico</label>
          <input name="email" type="email" className="ui-input" placeholder="tu@email.com" required />
        </div>
        <div className="group">
          <label>Contraseña</label>
          <input name="password" type="password" className="ui-input" placeholder="••••••••" required />
        </div>
      </AuthScreen>
    )
  }

  if (pathname === '/register') {
    return (
      <AuthScreen title="Únete a la" titleGold="élite" subtitle="Crea tu cuenta premium" submit="Crear Cuenta">
        <div className="group">
          <label>Nombre Completo</label>
          <input name="name" type="text" className="ui-input" placeholder="Ej: Juan Pérez" required />
        </div>
        <div className="group">
          <label>Correo Electrónico</label>
          <input name="email" type="email" className="ui-input" placeholder="tu@email.com" required />
        </div>
        <div className="group">
          <label>Contraseña</label>
          <input name="password" type="password" className="ui-input" placeholder="••••••••" required />
        </div>
      </AuthScreen>
    )
  }

  const renderContent = () => {
    if (pathname.startsWith('/dashboard')) {
      const roleMap = { admin: 'Administrativo', barber: 'Profesional', client: 'Cliente' }
      let resolvedRole = roleMap[storedUser?.role || jwtPayload?.role] || 'Cliente'

      // Override by path segment only when the path explicitly targets a role namespace
      // e.g. /dashboard/admin/... or /dashboard/barber/... or /dashboard/client/...
      const pathSegments = pathname.split('/').filter(Boolean) // ['dashboard','admin','appointments']
      const roleSegment = pathSegments[1]
      if (roleSegment === 'admin') resolvedRole = 'Administrativo'
      else if (roleSegment === 'barber') resolvedRole = 'Profesional'
      else if (roleSegment === 'client') resolvedRole = 'Cliente'

      // Determine subview from path
      const segments = pathname.split('/').filter(Boolean) // ['dashboard','admin','appointments']
      const lastSegment = segments[segments.length - 1]
      const knownViews = [
        'overview','appointments','services','clients','barbers','users',
        'payments','inventory','reports','predictions','settings','logs',
        'agenda','schedule','portfolio','profile','booking','history','notifications'
      ]
      const prefixes = ['admin','barber','client','dashboard']
      const view = knownViews.includes(lastSegment) && !prefixes.includes(lastSegment) ? lastSegment : 'overview'

      return <DashboardScreen role={resolvedRole} subview={view} />
    }

    return <HomeScreen />
  }

  return (
    <>
      {renderContent()}
      <AIChatbot />
      <ToastContainer />
    </>
  )
}
