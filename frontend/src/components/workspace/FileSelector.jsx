import { useState, useRef } from 'react';
import { filesAPI } from '../../api/client';

export default function FileSelector({ onFilesChange }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileRef = useRef();

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setError('');
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      await filesAPI.upload(formData);
      onFilesChange();
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
      fileRef.current.value = '';
    }
  };

  return (
    <div>
      <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv,.pdf,.txt" onChange={handleUpload} style={{ display: 'none' }} />
      <button
        onClick={() => fileRef.current.click()}
        disabled={uploading}
        style={{
          width: '100%', padding: '9px 14px',
          background: uploading ? 'var(--bg-elevated)' : 'linear-gradient(135deg, #6366F1, #8B5CF6)',
          color: uploading ? 'var(--text-muted)' : '#fff',
          borderRadius: 'var(--radius-md)', fontSize: '13px', fontWeight: 600,
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
          transition: 'opacity 0.2s, transform 0.15s',
          cursor: uploading ? 'not-allowed' : 'pointer',
          border: uploading ? '1px solid var(--border)' : 'none',
          boxShadow: uploading ? 'none' : '0 2px 12px rgba(99,102,241,0.3)'
        }}
        onMouseEnter={e => { if (!uploading) e.currentTarget.style.opacity = '0.88'; }}
        onMouseLeave={e => { if (!uploading) e.currentTarget.style.opacity = '1'; }}
      >
        {uploading ? (
          <>
            <span style={{ width: '12px', height: '12px', border: '2px solid rgba(255,255,255,0.2)', borderTopColor: 'var(--text-secondary)', borderRadius: '50%', animation: 'spin 0.7s linear infinite', display: 'inline-block' }} />
            Processing...
          </>
        ) : (
          <>+ Upload File</>
        )}
      </button>
      {error && <div style={{ fontSize: '12px', color: 'var(--error)', marginTop: '6px', textAlign: 'center' }}>{error}</div>}
    </div>
  );
}
