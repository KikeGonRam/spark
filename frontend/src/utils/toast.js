/**
 * Minimal toast notification system using custom DOM events.
 * No React state / Context needed — any component can call toast().
 */

let _counter = 0

export function toast(message, type = 'info', duration = 3500) {
  const id = ++_counter
  window.dispatchEvent(
    new CustomEvent('barberpro:toast', {
      detail: { id, message, type, duration },
    })
  )
  return id
}

toast.success = (msg, d) => toast(msg, 'success', d)
toast.error   = (msg, d) => toast(msg, 'error',   d)
toast.warning = (msg, d) => toast(msg, 'warning', d)
toast.info    = (msg, d) => toast(msg, 'info',    d)
