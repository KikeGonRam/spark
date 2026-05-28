import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

vi.mock('../hooks/useNavigation', () => ({
  apiFetch: vi.fn(),
  navigate: vi.fn(),
  getStoredToken: vi.fn(() => 'mock-token'),
  getStoredUser: vi.fn(() => ({ role: 'admin', name: 'Admin Test' })),
}))
vi.mock('../utils/toast', () => ({
  toast: Object.assign(vi.fn(), {
    success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn(),
  }),
}))
// Modal just renders children
vi.mock('../components/Modal', () => ({
  default: ({ isOpen, children, title, actions }) =>
    isOpen ? <div data-testid="modal"><h2>{title}</h2>{children}{actions}</div> : null,
}))

import AdminUsers from '../screens/admin/AdminUsers'
import AdminServices from '../screens/admin/AdminServices'
import AdminPayments from '../screens/admin/AdminPayments'
import { apiFetch } from '../hooks/useNavigation'
import { toast } from '../utils/toast'

// ============================================================================
// Admin Users
// ============================================================================
describe('AdminUsers', () => {
  const mockUsers = [
    { id: '1', name: 'Admin User', email: 'admin@test.com', role: 'admin', is_active: true },
    { id: '2', name: 'Barber User', email: 'barber@test.com', role: 'barber', is_active: true },
    { id: '3', name: 'Client User', email: 'client@test.com', role: 'client', is_active: false },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    apiFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, data: { users: mockUsers } }),
    })
  })

  it('renders user management title', async () => {
    render(<AdminUsers />)
    await waitFor(() => {
      expect(screen.getByText(/usuarios/i)).toBeInTheDocument()
    })
  })

  it('displays user list after loading', async () => {
    render(<AdminUsers />)
    await waitFor(() => {
      expect(screen.getByText('Admin User')).toBeInTheDocument()
      expect(screen.getByText('Barber User')).toBeInTheDocument()
      expect(screen.getByText('Client User')).toBeInTheDocument()
    })
  })

  it('shows role counts in KPI cards', async () => {
    render(<AdminUsers />)
    await waitFor(() => {
      // 1 admin, 1 barber, 1 client
      expect(screen.getAllByText('1')[0]).toBeTruthy()
    })
  })

  it('opens create modal on button click', async () => {
    render(<AdminUsers />)
    await waitFor(() => screen.getByText('Admin User'))
    fireEvent.click(screen.getByText('+ Nuevo Usuario'))
    expect(screen.getByTestId('modal')).toBeInTheDocument()
    expect(screen.getByText('Nuevo Usuario')).toBeInTheDocument()
  })

  it('shows success toast after saving user', async () => {
    apiFetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ data: { users: mockUsers } }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ data: { users: mockUsers } }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ data: { users: mockUsers } }) })

    render(<AdminUsers />)
    await waitFor(() => screen.getByText('Admin User'))
    fireEvent.click(screen.getByText('+ Nuevo Usuario'))
    fireEvent.click(screen.getByText('Guardar'))

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('guardado'))
    })
  })

  it('shows error toast on API failure', async () => {
    apiFetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ data: { users: mockUsers } }) })
      .mockResolvedValueOnce({ ok: false, json: async () => ({ detail: 'Error de servidor' }) })

    render(<AdminUsers />)
    await waitFor(() => screen.getByText('Admin User'))
    fireEvent.click(screen.getByText('+ Nuevo Usuario'))
    fireEvent.click(screen.getByText('Guardar'))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(expect.stringContaining('Error'))
    })
  })
})


// ============================================================================
// Admin Services
// ============================================================================
describe('AdminServices', () => {
  const mockServices = [
    { id: 's1', name: 'Corte Clásico', price: 50, duration: 30, category: 'haircut', is_active: true },
    { id: 's2', name: 'Barba y Bigote', price: 35, duration: 20, category: 'beard', is_active: true },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    apiFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, data: { services: mockServices } }),
    })
  })

  it('renders services title', async () => {
    render(<AdminServices />)
    await waitFor(() => expect(screen.getByText(/servicios/i)).toBeInTheDocument())
  })

  it('displays service list', async () => {
    render(<AdminServices />)
    await waitFor(() => {
      expect(screen.getByText('Corte Clásico')).toBeInTheDocument()
      expect(screen.getByText('Barba y Bigote')).toBeInTheDocument()
    })
  })

  it('shows service prices', async () => {
    render(<AdminServices />)
    await waitFor(() => {
      expect(screen.getByText('$50')).toBeInTheDocument()
      expect(screen.getByText('$35')).toBeInTheDocument()
    })
  })

  it('opens new service modal', async () => {
    render(<AdminServices />)
    await waitFor(() => screen.getByText('Corte Clásico'))
    fireEvent.click(screen.getByText('+ Nuevo Servicio'))
    expect(screen.getByTestId('modal')).toBeInTheDocument()
  })
})


// ============================================================================
// Admin Payments
// ============================================================================
describe('AdminPayments', () => {
  const mockPayments = [
    { id: 'p1', customer_name: 'Juan Pérez', amount: 50, tip: 5, method: 'cash', status: 'completed', created_at: '2026-05-01' },
    { id: 'p2', customer_name: 'Ana García', amount: 35, tip: 0, method: 'credit_card', status: 'pending', created_at: '2026-05-02' },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    apiFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, data: mockPayments }),
    })
  })

  it('renders payments title', async () => {
    render(<AdminPayments />)
    await waitFor(() => expect(screen.getByText(/pagos/i)).toBeInTheDocument())
  })

  it('shows revenue KPI (only completed payments)', async () => {
    render(<AdminPayments />)
    await waitFor(() => {
      // Only p1 (completed) counts: $50.00 (KPI and table row)
      expect(screen.getAllByText('$50.00')[0]).toBeInTheDocument()
    })
  })

  it('shows total tips KPI', async () => {
    render(<AdminPayments />)
    await waitFor(() => {
      expect(screen.getByText('$5.00')).toBeInTheDocument()
    })
  })

  it('renders payment rows', async () => {
    render(<AdminPayments />)
    await waitFor(() => {
      expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
      expect(screen.getByText('Ana García')).toBeInTheDocument()
    })
  })

  it('opens register payment modal', async () => {
    render(<AdminPayments />)
    await waitFor(() => screen.getByText('Juan Pérez'))
    fireEvent.click(screen.getByText('+ Registrar Pago'))
    expect(screen.getByTestId('modal')).toBeInTheDocument()
  })
})
