import { useAuth } from '../../context/AuthContext';
import FileSelector from '../workspace/FileSelector';

const FILE_TYPE_COLORS = {
  excel: '#4CAF7D',
  csv: '#4CAF7D',
  pdf: '#E8A84A',
  text: '#A09890'
};

const FILE_TYPE_LABELS = {
  excel: 'XLS',
  csv: 'CSV',
  pdf: 'PDF',
  text: 'TXT'
};

export default function Sidebar({ files, selectedWorkspace, onSelectWorkspace, onFilesChange, isOpen, onToggle }) {
  const { user, logout } = useAuth();

  return (
    <div style={{
      width: isOpen ? '280px' : '0px', minWidth: isOpen ? '280px' : '0px',
      height: '100vh', background: '#1A1814',
      borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      transition: 'width 0.3s ease, min-width 0.3s ease',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px', height: '32px', background: 'var(--accent)',
            borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0
          }}>
            <span style={{ fontSize: '16px' }}>⬡</span>
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>HybridRAG</div>
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>{user?.email}</div>
          </div>
        </div>
      </div>

      {/* File list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '4px 8px 8px' }}>
          Workspaces
        </div>
        {files.length === 0 ? (
          <div style={{ padding: '20px 8px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '13px' }}>
            No files yet. Upload to get started.
          </div>
        ) : (
          files.map(ws => (
            <div
              key={ws.workspace_id}
              onClick={() => onSelectWorkspace(ws)}
              style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                padding: '10px 12px', borderRadius: 'var(--radius-md)',
                cursor: 'pointer', marginBottom: '2px',
                background: selectedWorkspace?.workspace_id === ws.workspace_id
                  ? 'var(--accent-muted)' : 'transparent',
                border: selectedWorkspace?.workspace_id === ws.workspace_id
                  ? '1px solid rgba(217,119,87,0.2)' : '1px solid transparent',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={e => {
                if (selectedWorkspace?.workspace_id !== ws.workspace_id)
                  e.currentTarget.style.background = 'var(--bg-card-hover)';
              }}
              onMouseLeave={e => {
                if (selectedWorkspace?.workspace_id !== ws.workspace_id)
                  e.currentTarget.style.background = 'transparent';
              }}
            >
              <span style={{
                fontSize: '10px', fontWeight: 700,
                color: FILE_TYPE_COLORS[ws.file_type],
                background: `${FILE_TYPE_COLORS[ws.file_type]}20`,
                padding: '2px 5px', borderRadius: '4px', flexShrink: 0
              }}>
                {FILE_TYPE_LABELS[ws.file_type]}
              </span>
              <span style={{
                fontSize: '13px', color: 'var(--text-primary)',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
              }}>
                {ws.filename}
              </span>
            </div>
          ))
        )}
      </div>

      {/* File Upload + Logout */}
      <div style={{ padding: '12px', borderTop: '1px solid var(--border)' }}>
        <FileSelector onFilesChange={onFilesChange} />
        <button
          onClick={logout}
          style={{
            width: '100%', padding: '9px', marginTop: '8px',
            background: 'transparent', color: 'var(--text-tertiary)',
            borderRadius: 'var(--radius-md)', fontSize: '13px',
            border: '1px solid var(--border)', transition: 'all 0.15s ease'
          }}
          onMouseEnter={e => { e.target.style.color = 'var(--error)'; e.target.style.borderColor = 'var(--error)'; }}
          onMouseLeave={e => { e.target.style.color = 'var(--text-tertiary)'; e.target.style.borderColor = 'var(--border)'; }}
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
