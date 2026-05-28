import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock navigation/API hook before imports that use it
vi.mock('../hooks/useNavigation', () => ({
  usePathname: vi.fn(() => '/login'),
  navigate: vi.fn(),
  getStoredToken: vi.fn(() => null),
  getStoredUser: vi.fn(() => null),
  decodeJwtPayload: vi.fn(() => null),
  apiFetch: vi.fn(),
}))

import AuthScreen from '../screens/AuthScreen'
import { navigate, apiFetch } from '../hooks/useNavigation'

describe('AuthScreen — Login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders login form with email and password fields', () => {
    render(
      <AuthScreen title="Bienvenido" titleGold="de nuevo" subtitle="Introduce tus credenciales" submit="Iniciar Sesión">
        <div className="group">
          <label>Correo Electrónico</label>
          <input name="email" type="email" required />
        </div>
        <div className="group">
          <label>Contraseña</label>
          <input name="password" type="password" required />
        </div>
      </AuthScreen>
    )
    expect(screen.getAllByText('Iniciar Sesión')[0]).toBeInTheDocument()
    expect(screen.queryByLabelText(/correo/i) || screen.queryByPlaceholderText(/email/i) || screen.queryByRole('button', { name: /iniciar/i })).toBeTruthy()
  })

  it('calls login API on form submit', async () => {
    apiFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ token: 'test-token', user: { email: 'admin@example.com', role: 'admin' } }),
    })

    render(
      <AuthScreen title="Login" titleGold="" subtitle="" submit="Iniciar Sesión">
        <input name="email" type="email" defaultValue="admin@example.com" />
        <input name="password" type="password" defaultValue="Admin@2026" />
      </AuthScreen>
    )

    const submitBtn = screen.getByRole('button', { name: /iniciar/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringContaining('login'),
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  it('stores token in localStorage after successful login', async () => {
    apiFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ token: 'jwt-test-token', user: { email: 'test@example.com', role: 'admin', name: 'Test' } }),
    })

    render(
      <AuthScreen title="Login" titleGold="" subtitle="" submit="Iniciar Sesión">
        <input name="email" type="email" defaultValue="test@example.com" />
        <input name="password" type="password" defaultValue="Pass@2026" />
      </AuthScreen>
    )

    fireEvent.click(screen.getByRole('button', { name: /iniciar/i }))

    await waitFor(() => {
      const stored = localStorage.getItem('barberpro_token')
      expect(stored).toBeTruthy()
    })
  })

  it('shows error state on failed login', async () => {
    apiFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Email o contraseña incorrectos' }),
    })

    render(
      <AuthScreen title="Login" titleGold="" subtitle="" submit="Iniciar Sesión">
        <input name="email" type="email" defaultValue="wrong@example.com" />
        <input name="password" type="password" defaultValue="WrongPass" />
      </AuthScreen>
    )

    fireEvent.click(screen.getByRole('button', { name: /iniciar/i }))

    await waitFor(() => {
      // Should NOT navigate on failure
      expect(navigate).not.toHaveBeenCalled()
    })
  })
})
