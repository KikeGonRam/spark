import { useEffect } from 'react'
import { createPortal } from 'react-dom'

export default function Modal({ isOpen, onClose, title, children, actions }) {
    useEffect(() => {
        if (!isOpen) return
        const onKey = (e) => { if (e.key === 'Escape') onClose() }
        document.addEventListener('keydown', onKey)
        return () => document.removeEventListener('keydown', onKey)
    }, [isOpen, onClose])

    if (!isOpen) return null

    return createPortal(
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-card animate-slide-up" onClick={e => e.stopPropagation()}>
                <div className="modal-head">
                    <h3 className="ui-profile-title" style={{ fontSize: '1.25rem' }}>{title}</h3>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: 'var(--muted)', lineHeight: 1 }}>&times;</button>
                </div>
                <div className="modal-body">
                    {children}
                </div>
                {actions && (
                    <div className="modal-actions">
                        {actions}
                    </div>
                )}
            </div>
        </div>,
        document.body
    )
}
