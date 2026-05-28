import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act, waitFor } from '@testing-library/react'
import ToastContainer from '../components/ToastContainer'
import { toast } from '../utils/toast'

describe('Toast notification system', () => {
  beforeEach(() => {
    // Restore real event dispatching for toast tests
    window.dispatchEvent = window.dispatchEvent.bind(window)
    window.addEventListener = window.addEventListener.bind(window)
  })

  it('toast.success dispatches custom event with correct type', () => {
    const handler = vi.fn()
    window.addEventListener('barberpro:toast', handler)
    toast.success('Operación exitosa')
    expect(handler).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: expect.objectContaining({ type: 'success', message: 'Operación exitosa' }),
      })
    )
    window.removeEventListener('barberpro:toast', handler)
  })

  it('toast.error dispatches event with error type', () => {
    const handler = vi.fn()
    window.addEventListener('barberpro:toast', handler)
    toast.error('Ha ocurrido un error')
    expect(handler).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: expect.objectContaining({ type: 'error', message: 'Ha ocurrido un error' }),
      })
    )
    window.removeEventListener('barberpro:toast', handler)
  })

  it('toast.warning dispatches event with warning type', () => {
    const handler = vi.fn()
    window.addEventListener('barberpro:toast', handler)
    toast.warning('Advertencia')
    expect(handler).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: expect.objectContaining({ type: 'warning' }),
      })
    )
    window.removeEventListener('barberpro:toast', handler)
  })

  it('each toast call increments id', () => {
    const ids = []
    const handler = (e) => ids.push(e.detail.id)
    window.addEventListener('barberpro:toast', handler)
    toast('First')
    toast('Second')
    expect(ids[1]).toBeGreaterThan(ids[0])
    window.removeEventListener('barberpro:toast', handler)
  })

  it('ToastContainer renders toast messages', async () => {
    render(<ToastContainer />)
    act(() => { toast.success('Toast visible') })
    await waitFor(() => {
      expect(screen.getByText('Toast visible')).toBeInTheDocument()
    })
  })

  it('ToastContainer shows multiple toasts', async () => {
    render(<ToastContainer />)
    act(() => {
      toast.success('First message')
      toast.error('Second message')
    })
    await waitFor(() => {
      expect(screen.getByText('First message')).toBeInTheDocument()
      expect(screen.getByText('Second message')).toBeInTheDocument()
    })
  })
})
