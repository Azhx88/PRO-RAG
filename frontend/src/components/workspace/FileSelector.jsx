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
      <input
        ref={fileRef} type="file"
        accept=".xlsx,.xls,.csv,.pdf,.txt"
        onChange={handleUpload}
        style={{ display: 'none' }}
      />
      <button
        onClick={() => fileRef.current.click()}
        disabled={uploading}
        style={{
          width: '100%', padding: '10px',
          background: uploading ? 'var(--text-tertiary)' : 'var(--accent)',
          color: '#fff', borderRadius: 'var(--radius-md)',
          fontSize: '13px', fontWeight: 600,
          transition: 'background 0.2s',
          cursor: uploading ? 'not-allowed' : 'pointer'
        }}
        onMouseEnter={e => { if (!uploading) e.target.style.background = 'var(--accent-hover)'; }}
        onMouseLeave={e => { if (!uploading) e.target.style.background = 'var(--accent)'; }}
      >
        {uploading ? 'Processing...' : '+ Upload File'}
      </button>
      {error && <div style={{ fontSize: '12px', color: 'var(--error)', marginTop: '6px' }}>{error}</div>}
    </div>
  );
}
