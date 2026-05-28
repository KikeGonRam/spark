export const API_BASE = '/api'

export const services = [
  { title: 'Corte Signature', price: '$320', time: '45 Min', desc: 'Una experiencia diseñada para resaltar tu mejor versión con técnica clásica.' },
  { title: 'Barba Ritual', price: '$220', time: '30 Min', desc: 'Tratamiento completo con toallas calientes y aceites esenciales premium.' },
  { title: 'Combo Elite', price: '$480', time: '60 Min', desc: 'El ritual definitivo: Corte signature y arreglo de barba magistral.' },
]

export const barbers = [
  { initials: 'JP', name: 'Juan Pérez', role: 'Master Groomer' },
  { initials: 'MR', name: 'Mario Ruiz', role: 'Senior Barber' },
  { initials: 'AL', name: 'Alex León', role: 'Style Specialist' },
  { initials: 'CV', name: 'Carlos Vela', role: 'Fade Expert' },
]

export const kpis = [
  { label: 'Citas hoy', value: '18' },
  { label: 'Ingresos hoy', value: '$1,240' },
  { label: 'Clientes activos', value: '326' },
  { label: 'Retención', value: '84.2%' },
]

export const dashboardLinks = [
  { path: '/dashboard/admin', label: 'Admin' },
  { path: '/dashboard/barber', label: 'Barber' },
  { path: '/dashboard/client', label: 'Client' },
]
