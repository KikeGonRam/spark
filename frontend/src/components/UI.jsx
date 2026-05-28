export function Badge({ children, className = "" }) { 
  return <span className={`ui-badge ${className}`}>{children}</span> 
}

export function SectionHeader({ title, subtitle, light = false }) { 
  return (
    <div className="section-header">
      <p>{subtitle}</p>
      <h2 className={light ? "" : "text-white"}>{title}</h2>
      <div style={{ marginTop: '20px', height: '2px', width: '60px', background: 'var(--gold)', margin: '20px auto 0' }}></div>
    </div>
  )
}
