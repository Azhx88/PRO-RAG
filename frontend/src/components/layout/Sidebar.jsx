import { useAuth } from '../../context/AuthContext';
import FileSelector from '../workspace/FileSelector';

const TYPE_CONFIG = {
  excel: { label: 'XLS', color: '#10B981', bg: 'rgba(16,185,129,0.12)' },
  csv:   { label: 'CSV', color: '#10B981', bg: 'rgba(16,185,129,0.12)' },
  pdf:   { label: 'PDF', color: '#F59E0B', bg: 'rgba(245,158,11,0.12)' },
  text:  { label: 'TXT', color: '#94A3B8', bg: 'rgba(148,163,184,0.1)' },
};

export default function Sidebar({ files, selectedWorkspace, onSelectWorkspace, onFilesChange, isOpen }) {
  const { user, logout } = useAuth();
  const initials = user?.email?.slice(0, 2).toUpperCase() || '??';

  return (
    <div style={{
      width: isOpen ? '260px' : '0px', minWidth: isOpen ? '260px' : '0px',
      height: '100vh', background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      transition: 'width 0.25s ease, min-width 0.25s ease',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{ padding: '20px 16px 16px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '34px', height: '34px', background: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
            borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0, fontSize: '15px', boxShadow: '0 4px 12px rgba(99,102,241,0.3)'
          }}>✦</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)', letterSpacing: '-0.2px' }}>HybridRAG</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '1px' }}>{user?.email}</div>
          </div>
        </div>
      </div>

      {/* Workspace list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '10px 10px' }}>
        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '6px 8px 8px' }}>
          Workspaces
        </div>

        {files.length === 0 ? (
          <div style={{ padding: '24px 8px', textAlign: 'center' }}>
            <div style={{ fontSize: '28px', marginBottom: '10px', opacity: 0.3 }}>📂</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '12px', lineHeight: 1.6 }}>
              No files yet.<br />Upload one to get started.
            </div>
          </div>
        ) : (
          files.map(ws => {
            const tc = TYPE_CONFIG[ws.file_type] || TYPE_CONFIG.text;
            const isActive = selectedWorkspace?.workspace_id === ws.workspace_id;
            return (
              <div
                key={ws.workspace_id}
                onClick={() => onSelectWorkspace(ws)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '9px',
                  padding: '9px 10px', borderRadius: 'var(--radius-md)',
                  cursor: 'pointer', marginBottom: '2px',
                  background: isActive ? 'rgba(99,102,241,0.12)' : 'transparent',
                  border: isActive ? '1px solid rgba(99,102,241,0.25)' : '1px solid transparent',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = 'var(--bg-card-hover)'; }}
                onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent'; }}
              >
                <span style={{ fontSize: '10px', fontWeight: 700, color: tc.color, background: tc.bg, padding: '2px 6px', borderRadius: '4px', flexShrink: 0, letterSpacing: '0.03em' }}>
                  {tc.label}
                </span>
                <span style={{ fontSize: '13px', color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                  {ws.filename}
                </span>
                {isActive && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent)', flexShrink: 0 }} />}
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div style={{ padding: '12px', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
        <FileSelector onFilesChange={onFilesChange} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px', padding: '8px 10px', borderRadius: 'var(--radius-md)', cursor: 'pointer', transition: 'all 0.15s' }}
          onMouseEnter={e => { e.currentTarget.style.background = 'var(--error-muted)'; e.currentTarget.querySelector('span').style.color = 'var(--error)'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.querySelector('span').style.color = 'var(--text-muted)'; }}
          onClick={logout}
        >
          <div style={{ width: '26px', height: '26px', borderRadius: '8px', background: 'var(--bg-elevated)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)' }}>
            {initials}
          </div>
          <span style={{ fontSize: '13px', color: 'var(--text-muted)', transition: 'color 0.15s' }}>Sign out</span>
        </div>
      </div>
    </div>
  );
}
