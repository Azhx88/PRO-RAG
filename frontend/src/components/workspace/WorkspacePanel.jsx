export default function WorkspacePanel() {
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: '48px', textAlign: 'center', background: 'var(--bg-base)',
      position: 'relative', overflow: 'hidden'
    }}>
      {/* Background glow */}
      <div style={{ position: 'absolute', width: '500px', height: '500px', background: 'radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 65%)', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', pointerEvents: 'none' }} />

      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{
          width: '68px', height: '68px', background: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
          borderRadius: '22px', display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 24px', fontSize: '30px', boxShadow: '0 8px 32px rgba(99,102,241,0.3)'
        }}>✦</div>

        <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '10px', letterSpacing: '-0.3px' }}>
          Select a workspace
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '340px', fontSize: '14px', lineHeight: 1.7, margin: '0 auto 36px' }}>
          Upload a file from the sidebar, then ask any question. Queries are automatically routed to the right pipeline.
        </p>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
          {[
            { icon: '📊', label: 'Excel / CSV', desc: 'SQL retrieval + charts', color: '#10B981', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.2)' },
            { icon: '📄', label: 'PDF / Text',  desc: 'Semantic vector search',  color: '#F59E0B', bg: 'rgba(245,158,11,0.08)',  border: 'rgba(245,158,11,0.2)' },
          ].map(item => (
            <div key={item.label} style={{
              padding: '18px 22px', background: item.bg, borderRadius: 'var(--radius-xl)',
              border: `1px solid ${item.border}`, minWidth: '150px', textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>{item.icon}</div>
              <div style={{ fontWeight: 600, color: item.color, fontSize: '13px', marginBottom: '4px' }}>{item.label}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{item.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
