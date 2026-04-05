export default function TopBar({ onToggleSidebar }) {
  return (
    <div style={{
      height: '48px', display: 'flex', alignItems: 'center',
      padding: '0 16px', borderBottom: '1px solid var(--border)',
      background: '#1A1814'
    }}>
      <button
        onClick={onToggleSidebar}
        style={{
          background: 'transparent', color: 'var(--text-secondary)',
          fontSize: '18px', padding: '4px 8px', borderRadius: 'var(--radius-sm)',
          transition: 'color 0.15s ease'
        }}
        onMouseEnter={e => e.target.style.color = 'var(--text-primary)'}
        onMouseLeave={e => e.target.style.color = 'var(--text-secondary)'}
      >
        ☰
      </button>
    </div>
  );
}
