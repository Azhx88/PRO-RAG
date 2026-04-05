const API_BASE = 'http://localhost:8000';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const meta = message.metadata;

  return (
    <div className="msg-enter" style={{
      display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: '20px', gap: '10px',
      flexDirection: isUser ? 'row-reverse' : 'row', alignItems: 'flex-start'
    }}>
      {/* Avatar */}
      <div style={{
        width: '30px', height: '30px', borderRadius: '9px', flexShrink: 0,
        background: isUser ? 'linear-gradient(135deg, #6366F1, #8B5CF6)' : 'var(--bg-elevated)',
        border: isUser ? 'none' : '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '12px', boxShadow: isUser ? '0 2px 8px rgba(99,102,241,0.3)' : 'none'
      }}>
        {isUser ? '↑' : '✦'}
      </div>

      <div style={{ maxWidth: '72%', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {/* Bubble */}
        <div style={{
          padding: '12px 16px',
          background: isUser ? 'linear-gradient(135deg, rgba(99,102,241,0.18), rgba(139,92,246,0.18))' : 'var(--bg-card)',
          border: `1px solid ${isUser ? 'rgba(99,102,241,0.2)' : 'var(--border)'}`,
          borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
          fontSize: '14px', lineHeight: 1.7, color: 'var(--text-primary)',
          whiteSpace: 'pre-wrap', wordBreak: 'break-word'
        }}>
          {message.content}
        </div>

        {/* SQL block */}
        {meta?.sql && (
          <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', overflow: 'hidden' }}>
            <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981', display: 'inline-block' }} />
              <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>GENERATED SQL</span>
            </div>
            <pre style={{ margin: 0, padding: '12px 14px', background: 'var(--bg-input)', color: '#7DD3FC', fontSize: '12px', overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontFamily: "'JetBrains Mono', 'Fira Code', monospace", lineHeight: 1.6 }}>
              {meta.sql}
            </pre>
          </div>
        )}

        {/* Results table */}
        {meta?.results_preview?.length > 0 && (
          <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', overflow: 'hidden' }}>
            <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
                <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>RESULTS</span>
              </div>
              {meta.row_count !== undefined && (
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.04)', padding: '2px 8px', borderRadius: '10px' }}>
                  {meta.row_count} rows
                </span>
              )}
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    {Object.keys(meta.results_preview[0]).map(col => (
                      <th key={col} style={{ padding: '9px 14px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', fontSize: '10px', letterSpacing: '0.06em', textAlign: 'left', whiteSpace: 'nowrap' }}>
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {meta.results_preview.map((row, idx) => (
                    <tr key={idx} style={{ borderBottom: idx < meta.results_preview.length - 1 ? '1px solid rgba(255,255,255,0.03)' : 'none' }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                      {Object.values(row).map((val, vi) => (
                        <td key={vi} style={{ padding: '8px 14px', color: 'var(--text-secondary)' }}>
                          {val !== null && val !== undefined ? String(val) : <span style={{ color: 'var(--text-muted)' }}>—</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Chart */}
        {meta?.chart_path && (
          <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', overflow: 'hidden' }}>
            <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#F59E0B', display: 'inline-block' }} />
              <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>VISUALIZATION</span>
            </div>
            <div style={{ padding: '12px' }}>
              <img
                src={`${API_BASE}/charts/${meta.chart_path.split('/charts/')[1]}`}
                alt="Chart"
                style={{ width: '100%', borderRadius: 'var(--radius-md)', display: 'block' }}
              />
            </div>
          </div>
        )}

        {/* Sources for RAG */}
        {meta?.sources?.length > 0 && (
          <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', overflow: 'hidden' }}>
            <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#8B5CF6', display: 'inline-block' }} />
              <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>SOURCES</span>
            </div>
            <div style={{ padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {meta.sources.map((src, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{src.filename} · chunk {src.chunk_index}</span>
                  <span style={{ color: 'var(--accent)', fontWeight: 600, fontSize: '11px', background: 'var(--accent-muted)', padding: '2px 7px', borderRadius: '10px' }}>
                    {Math.round(src.score * 100)}% match
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
