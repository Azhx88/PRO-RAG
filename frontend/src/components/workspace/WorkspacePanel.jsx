export default function WorkspacePanel({ onFilesChange, onSelectWorkspace }) {
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: '48px', textAlign: 'center'
    }}>
      <div style={{
        width: '72px', height: '72px', background: 'var(--accent-muted)',
        borderRadius: '20px', display: 'flex', alignItems: 'center',
        justifyContent: 'center', marginBottom: '24px', fontSize: '36px'
      }}>
        ⬡
      </div>
      <h2 style={{ fontSize: '22px', fontWeight: 600, marginBottom: '12px' }}>Select a workspace</h2>
      <p style={{ color: 'var(--text-secondary)', maxWidth: '360px', fontSize: '14px', lineHeight: 1.7 }}>
        Upload an Excel, CSV, PDF, or text file from the sidebar. Then ask any question — the system will automatically route your query to SQL or RAG.
      </p>
      <div style={{
        marginTop: '40px', display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'center'
      }}>
        {[
          { label: 'Excel / CSV', desc: 'SQL retrieval + dashboard', color: '#4CAF7D' },
          { label: 'PDF / Text', desc: 'Vector RAG pipeline', color: '#E8A84A' }
        ].map(item => (
          <div key={item.label} style={{
            padding: '20px 24px', background: 'var(--bg-card)',
            borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)',
            minWidth: '160px'
          }}>
            <div style={{ fontWeight: 600, color: item.color, marginBottom: '6px' }}>{item.label}</div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{item.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
