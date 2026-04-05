import { exportAPI } from '../../api/client';

export default function ExportButton({ sessionId, workspaceId, disabled }) {
  const handleExport = async () => {
    if (!sessionId || disabled) return;
    try {
      const res = await exportAPI.exportExcel(sessionId, workspaceId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `rag_export_${Date.now()}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed', err);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={disabled || !sessionId}
      style={{
        padding: '8px 16px', background: disabled || !sessionId ? 'var(--text-tertiary)' : 'var(--accent)',
        color: '#fff', borderRadius: 'var(--radius-md)',
        fontSize: '13px', fontWeight: 600,
        transition: 'background 0.2s',
        cursor: disabled || !sessionId ? 'not-allowed' : 'pointer'
      }}
      onMouseEnter={e => { if (!disabled && sessionId) e.target.style.background = 'var(--accent-hover)'; }}
      onMouseLeave={e => { if (!disabled && sessionId) e.target.style.background = 'var(--accent)'; }}
    >
      Export to Excel
    </button>
  );
}
