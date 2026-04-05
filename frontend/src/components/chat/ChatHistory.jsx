export default function ChatHistory({ history, onSelectSession }) {
  if (!history || history.length === 0) {
    return (
      <div style={{ padding: '16px', color: 'var(--text-tertiary)', fontSize: '13px', textAlign: 'center' }}>
        No chat history yet.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '8px' }}>
      {history.map(session => (
        <div
          key={session.session_id}
          onClick={() => onSelectSession && onSelectSession(session)}
          style={{
            padding: '10px 12px', borderRadius: 'var(--radius-md)',
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            cursor: 'pointer', transition: 'all 0.15s ease'
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-card-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'var(--bg-card)'}
        >
          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '4px' }}>
            {new Date(session.created_at).toLocaleString()}
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {session.messages[0]?.content || 'Empty session'}
          </div>
        </div>
      ))}
    </div>
  );
}
