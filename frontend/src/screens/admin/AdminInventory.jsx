import { useEffect, useState } from 'react'
import { apiFetch } from '../../hooks/useNavigation'
import { toast } from '../../utils/toast'
import Modal from '../../components/Modal'

const CATEGORIES = ['hair_products', 'shaving_products', 'styling_products', 'tools', 'supplies']
const CATEGORY_LABELS = { hair_products: 'Productos Cabello', shaving_products: 'Productos Barba', styling_products: 'Styling', tools: 'Herramientas', supplies: 'Insumos' }

export default function AdminInventory() {
    const [tab, setTab] = useState('products')
    const [products, setProducts] = useState([])
    const [movements, setMovements] = useState([])
    const [loading, setLoading] = useState(true)
    const [isProductModal, setIsProductModal] = useState(false)
    const [isMovementModal, setIsMovementModal] = useState(false)
    const [editingProduct, setEditingProduct] = useState(null)

    const [productForm, setProductForm] = useState({
        name: '', sku: '', category: 'supplies', quantity: 0,
        minimum_quantity: 5, unit: 'pza', price: '', supplier: ''
    })
    const [movementForm, setMovementForm] = useState({
        product_id: '', type: 'in', quantity: 1, reason: '', notes: ''
    })

    const loadData = async () => {
        setLoading(true)
        try {
            const [pRes, mRes] = await Promise.all([
                apiFetch('/inventory/products').then(r => r.json()),
                apiFetch('/inventory/movements').then(r => r.json())
            ])
            setProducts(pRes.data?.products || pRes.data || [])
            setMovements(mRes.data?.movements || mRes.data || [])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { loadData() }, [])

    const openProductModal = (p = null) => {
        if (p) {
            setEditingProduct(p)
            setProductForm({ name: p.name || '', sku: p.sku || '', category: p.category || 'supplies', quantity: p.quantity || 0, minimum_quantity: p.minimum_quantity || 5, unit: p.unit || 'pza', price: p.price || '', supplier: p.supplier || '' })
        } else {
            setEditingProduct(null)
            setProductForm({ name: '', sku: '', category: 'supplies', quantity: 0, minimum_quantity: 5, unit: 'pza', price: '', supplier: '' })
        }
        setIsProductModal(true)
    }

    const saveProduct = async (e) => {
        e.preventDefault()
        const method = editingProduct ? 'PUT' : 'POST'
        const url = editingProduct ? `/inventory/products/${editingProduct.id}` : '/inventory/products'
        const payload = { ...productForm, price: parseFloat(productForm.price), quantity: parseInt(productForm.quantity), minimum_quantity: parseInt(productForm.minimum_quantity) }
        const res = await apiFetch(url, { method, body: JSON.stringify(payload) })
        if (res.ok) { setIsProductModal(false); loadData(); toast.success('Producto guardado') }
        else { const e = await res.json(); toast.error(e.detail || 'Error al guardar') }
    }

    const deleteProduct = async (id) => {
        if (!window.confirm('¿Eliminar producto?')) return
        await apiFetch(`/inventory/products/${id}`, { method: 'DELETE' })
        loadData()
    }

    const saveMovement = async (e) => {
        e.preventDefault()
        const payload = { ...movementForm, quantity: parseInt(movementForm.quantity) }
        const res = await apiFetch('/inventory/movements', { method: 'POST', body: JSON.stringify(payload) })
        if (res.ok) { setIsMovementModal(false); loadData(); toast.success('Movimiento registrado') }
        else { const e = await res.json(); toast.error(e.detail || 'Error al registrar movimiento') }
    }

    const isLowStock = (p) => p.quantity <= (p.minimum_quantity || 5)

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="ui-profile-title">Control de <span className="text-gold">Inventario</span></h2>
                    <p className="ui-profile-subtitle">Gestión de productos e insumos</p>
                </div>
                <div className="flex gap-3">
                    <button onClick={() => setIsMovementModal(true)} className="ui-btn" style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)' }}>+ Movimiento</button>
                    <button onClick={() => openProductModal()} className="ui-btn-gold">+ Nuevo Producto</button>
                </div>
            </div>

            {/* Low stock alerts */}
            {products.filter(isLowStock).length > 0 && (
                <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '0.75rem', padding: '1rem 1.5rem' }}>
                    <p style={{ fontSize: '11px', fontWeight: 900, color: '#f87171', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                        ⚠️ {products.filter(isLowStock).length} producto(s) con stock bajo: {products.filter(isLowStock).map(p => p.name).join(', ')}
                    </p>
                </div>
            )}

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--line)', paddingBottom: '0' }}>
                {['products', 'movements'].map(t => (
                    <button key={t} onClick={() => setTab(t)} style={{ padding: '0.75rem 1.5rem', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.12em', background: 'transparent', border: 'none', cursor: 'pointer', color: tab === t ? 'var(--gold)' : 'var(--muted)', borderBottom: tab === t ? '2px solid var(--gold)' : '2px solid transparent', marginBottom: '-1px' }}>
                        {t === 'products' ? 'Productos' : 'Movimientos'}
                    </button>
                ))}
            </div>

            {tab === 'products' && (
                <section className="ui-card-premium">
                    <div className="ui-table-premium-wrapper">
                    <table className="ui-table-premium">
                        <thead>
                            <tr style={{ background: 'transparent' }}>
                                <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Producto</th>
                                <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>SKU</th>
                                <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Categoría</th>
                                <th style={{ textAlign: 'center', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Stock</th>
                                <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Precio</th>
                                <th style={{ textAlign: 'right', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {products.map((p, i) => (
                                <tr key={p.id ?? i}>
                                    <td>
                                        <div style={{ fontWeight: 800 }}>{p.name}</div>
                                        <div style={{ fontSize: '10px', color: '#555' }}>{p.supplier || 'Sin proveedor'}</div>
                                    </td>
                                    <td><span style={{ color: 'var(--muted)', fontSize: '11px', fontFamily: 'monospace' }}>{p.sku || '-'}</span></td>
                                    <td><span style={{ fontSize: '10px', color: 'var(--gold)' }}>{CATEGORY_LABELS[p.category] || p.category}</span></td>
                                    <td style={{ textAlign: 'center' }}>
                                        <span style={{ fontWeight: 900, color: isLowStock(p) ? '#f87171' : '#4ade80', fontSize: '14px' }}>{p.quantity}</span>
                                        <span style={{ fontSize: '9px', color: '#444', marginLeft: '4px' }}>{p.unit}</span>
                                        {isLowStock(p) && <div style={{ fontSize: '8px', color: '#f87171', fontWeight: 900 }}>STOCK BAJO</div>}
                                    </td>
                                    <td><span className="text-gold font-bold">${p.price || 0}</span></td>
                                    <td style={{ textAlign: 'right' }}>
                                        <button onClick={() => openProductModal(p)} className="ui-btn" style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.03)', marginRight: '8px' }}>Editar</button>
                                        <button onClick={() => deleteProduct(p.id)} className="ui-btn" style={{ padding: '6px 12px', color: '#f87171' }}>Borrar</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {loading && <p className="text-center py-12 text-muted animate-pulse">Sincronizando inventario...</p>}
                    {!loading && products.length === 0 && <p className="text-center py-12" style={{ color: 'var(--muted)' }}>Sin productos registrados.</p>}
                </div>
                </section>
            )}

            {tab === 'movements' && (
                <section className="ui-card-premium">
                    <div className="ui-table-premium-wrapper">
                    <table className="ui-table-premium">
                        <thead>
                            <tr style={{ background: 'transparent' }}>
                                <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Producto</th>
                                <th style={{ textAlign: 'center', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Tipo</th>
                                <th style={{ textAlign: 'center', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Cantidad</th>
                                <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Razón</th>
                                <th style={{ textAlign: 'left', padding: '1rem', fontSize: '10px', color: '#444', textTransform: 'uppercase' }}>Fecha</th>
                            </tr>
                        </thead>
                        <tbody>
                            {movements.map((m, i) => (
                                <tr key={m.id || i}>
                                    <td><div style={{ fontWeight: 800 }}>{m.product_name || m.product_id}</div></td>
                                    <td style={{ textAlign: 'center' }}>
                                        <span style={{ fontSize: '9px', fontWeight: 900, textTransform: 'uppercase', color: m.type === 'in' ? '#4ade80' : '#f87171', background: m.type === 'in' ? 'rgba(74,222,128,0.1)' : 'rgba(248,113,113,0.1)', padding: '3px 8px', borderRadius: '99px' }}>
                                            {m.type === 'in' ? '↑ Entrada' : '↓ Salida'}
                                        </span>
                                    </td>
                                    <td style={{ textAlign: 'center' }}><span style={{ fontWeight: 900 }}>{m.quantity}</span></td>
                                    <td><span style={{ color: 'var(--muted)', fontSize: '12px' }}>{m.reason || '-'}</span></td>
                                    <td><span style={{ color: 'var(--muted)', fontSize: '11px' }}>{m.created_at ? new Date(m.created_at).toLocaleDateString('es-MX') : '-'}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {loading && <p className="text-center py-12 text-muted animate-pulse">Cargando movimientos...</p>}
                    {!loading && movements.length === 0 && <p className="text-center py-12" style={{ color: 'var(--muted)' }}>Sin movimientos registrados.</p>}
                </div>
                </section>
            )}

            {/* Product Modal */}
            <Modal isOpen={isProductModal} onClose={() => setIsProductModal(false)} title={editingProduct ? 'Editar Producto' : 'Nuevo Producto'}
                actions={<><button onClick={() => setIsProductModal(false)} className="ui-btn" style={{ background: 'transparent' }}>Cancelar</button><button onClick={saveProduct} className="ui-btn-gold">Guardar</button></>}>
                <form className="space-y-4">
                    <div className="group"><label className="ui-kpi-label">Nombre del Producto</label>
                        <input className="ui-input" value={productForm.name} onChange={e => setProductForm({ ...productForm, name: e.target.value })} placeholder="Ej: Pomada Fijadora" required /></div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="group"><label className="ui-kpi-label">SKU</label>
                            <input className="ui-input" value={productForm.sku} onChange={e => setProductForm({ ...productForm, sku: e.target.value })} placeholder="PROD-001" /></div>
                        <div className="group"><label className="ui-kpi-label">Categoría</label>
                            <select className="ui-input" value={productForm.category} onChange={e => setProductForm({ ...productForm, category: e.target.value })}>
                                {CATEGORIES.map(c => <option key={c} value={c}>{CATEGORY_LABELS[c]}</option>)}</select></div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                        <div className="group"><label className="ui-kpi-label">Stock Actual</label>
                            <input type="number" className="ui-input" value={productForm.quantity} onChange={e => setProductForm({ ...productForm, quantity: e.target.value })} /></div>
                        <div className="group"><label className="ui-kpi-label">Stock Mínimo</label>
                            <input type="number" className="ui-input" value={productForm.minimum_quantity} onChange={e => setProductForm({ ...productForm, minimum_quantity: e.target.value })} /></div>
                        <div className="group"><label className="ui-kpi-label">Unidad</label>
                            <input className="ui-input" value={productForm.unit} onChange={e => setProductForm({ ...productForm, unit: e.target.value })} placeholder="pza" /></div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="group"><label className="ui-kpi-label">Precio ($)</label>
                            <input type="number" step="0.01" className="ui-input" value={productForm.price} onChange={e => setProductForm({ ...productForm, price: e.target.value })} placeholder="0.00" /></div>
                        <div className="group"><label className="ui-kpi-label">Proveedor</label>
                            <input className="ui-input" value={productForm.supplier} onChange={e => setProductForm({ ...productForm, supplier: e.target.value })} placeholder="Nombre del proveedor" /></div>
                    </div>
                </form>
            </Modal>

            {/* Movement Modal */}
            <Modal isOpen={isMovementModal} onClose={() => setIsMovementModal(false)} title="Registrar Movimiento"
                actions={<><button onClick={() => setIsMovementModal(false)} className="ui-btn" style={{ background: 'transparent' }}>Cancelar</button><button onClick={saveMovement} className="ui-btn-gold">Registrar</button></>}>
                <form className="space-y-4">
                    <div className="group"><label className="ui-kpi-label">Producto</label>
                        <select className="ui-input" value={movementForm.product_id} onChange={e => setMovementForm({ ...movementForm, product_id: e.target.value })} required>
                            <option value="">Seleccionar producto...</option>
                            {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="group"><label className="ui-kpi-label">Tipo</label>
                            <select className="ui-input" value={movementForm.type} onChange={e => setMovementForm({ ...movementForm, type: e.target.value })}>
                                <option value="in">Entrada</option><option value="out">Salida</option></select></div>
                        <div className="group"><label className="ui-kpi-label">Cantidad</label>
                            <input type="number" min="1" className="ui-input" value={movementForm.quantity} onChange={e => setMovementForm({ ...movementForm, quantity: e.target.value })} required /></div>
                    </div>
                    <div className="group"><label className="ui-kpi-label">Razón</label>
                        <input className="ui-input" value={movementForm.reason} onChange={e => setMovementForm({ ...movementForm, reason: e.target.value })} placeholder="Compra, uso en cita, ajuste..." /></div>
                    <div className="group"><label className="ui-kpi-label">Notas</label>
                        <textarea className="ui-input" value={movementForm.notes} onChange={e => setMovementForm({ ...movementForm, notes: e.target.value })} placeholder="Información adicional..." style={{ minHeight: '60px', resize: 'none' }} /></div>
                </form>
            </Modal>
        </div>
    )
}
