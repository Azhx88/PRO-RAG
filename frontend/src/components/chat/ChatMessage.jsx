const API_BASE = 'http://localhost:8000';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const meta = message.metadata;

  return (
    <div style={{
      display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: '16px', gap: '12px',
      flexDirection: isUser ? 'row-reverse' : 'row'
    }}>
      {/* Avatar */}
      <div style={{
        width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
        background: isUser ? 'var(--accent)' : 'var(--bg-card)',
        border: isUser ? 'none' : '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '14px', marginTop: '2px'
      }}>
        {isUser ? '●' : '⬡'}
      </div>

      {/* Bubble */}
      <div style={{ maxWidth: '70%', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{
          padding: '14px 18px',
          background: isUser ? 'rgba(217,119,87,0.15)' : 'var(--bg-card)',
          border: `1px solid ${isUser ? 'rgba(217,119,87,0.25)' : 'var(--border)'}`,
          borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
          fontSize: '14px', lineHeight: 1.7, color: 'var(--text-primary)',
          whiteSpace: 'pre-wrap', wordBreak: 'break-word'
        }}>
          {message.content}
        </div>

        {/* SQL badge */}
        {meta?.sql && (
          <div style={{ marginTop: '12px', background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', overflow: 'hidden' }}>
            <div style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', fontWeight: 'bold', letterSpacing: '0.5px', color: 'var(--text-secondary)' }}>
              <span>📊 GENERATED SQL</span>
            </div>
            <pre style={{ margin: 0, padding: '12px', background: 'var(--bg-input)', color: 'var(--accent)', fontSize: '13px', overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              {meta.sql}
            </pre>
          </div>
        )}

        {/* Custom Data Table */}
        {meta?.results_preview && meta.results_preview.length > 0 && (
          <div style={{ marginTop: '12px', background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', overflow: 'hidden' }}>
            <div style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', fontWeight: 'bold', letterSpacing: '0.5px', color: 'var(--text-secondary)' }}>
              <span>📄 RESULTS</span>
              {meta?.row_count !== undefined && (
                <span style={{ fontWeight: 'normal', color: 'var(--text-tertiary)', background: 'rgba(0,0,0,0.2)', padding: '2px 8px', borderRadius: '10px' }}>
                  {meta.row_count} rows returned
                </span>
              )}
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    {Object.keys(meta.results_preview[0]).map(col => (
                      <th key={col} style={{ padding: '10px 12px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', fontSize: '11px', letterSpacing: '0.5px' }}>
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {meta.results_preview.map((row, idx) => (
                    <tr key={idx} style={{ borderBottom: idx === meta.results_preview.length - 1 ? 'none' : '1px solid rgba(255,255,255,0.05)' }}>
                      {Object.values(row).map((val, vIdx) => (
                        <td key={vIdx} style={{ padding: '8px 12px', color: 'var(--text-primary)' }}>
                          {val !== null && val !== undefined ? String(val) : '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Chart image */}
        {meta?.chart_path && (
          <div style={{ marginTop: '12px', background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', overflow: 'hidden' }}>
             <div style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', fontSize: '11px', fontWeight: 'bold', letterSpacing: '0.5px', color: 'var(--text-secondary)' }}>
              <span>📈 VISUALIZATION</span>
            </div>
            <div style={{ padding: '12px', background: 'var(--bg-input)' }}>
              <img
                src={`${API_BASE}/charts/${meta.chart_path.split('/charts/')[1]}`}
                alt="Generated chart"
                style={{
                  width: '100%', borderRadius: 'var(--radius-md)',
                  display: 'block'
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
