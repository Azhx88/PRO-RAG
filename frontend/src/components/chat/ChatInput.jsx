import { useState, useRef } from 'react';

export default function ChatInput({ onSend, loading }) {
  const [query, setQuery] = useState('');
  const textareaRef = useRef();

  const handleSend = () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setQuery('');
    textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e) => {
    setQuery(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
  };

  return (
    <div style={{
      padding: '16px 24px', borderTop: '1px solid var(--border)',
      background: '#1A1814'
    }}>
      <div style={{
        display: 'flex', gap: '12px', alignItems: 'flex-end',
        background: 'var(--bg-input)', borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border)', padding: '12px 16px',
        transition: 'border-color 0.2s',
      }}>
        <textarea
          ref={textareaRef}
          value={query}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about this file... (Shift+Enter for new line)"
          rows={1}
          style={{
            flex: 1, background: 'transparent', border: 'none',
            color: 'var(--text-primary)', fontSize: '14px', lineHeight: 1.6,
            resize: 'none', outline: 'none', maxHeight: '160px',
            overflowY: 'auto', fontFamily: 'inherit'
          }}
        />
        <button
          onClick={handleSend}
          disabled={!query.trim() || loading}
          style={{
            width: '36px', height: '36px', flexShrink: 0,
            background: !query.trim() || loading ? 'var(--bg-card)' : 'var(--accent)',
            borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'background 0.2s', fontSize: '16px',
            cursor: !query.trim() || loading ? 'not-allowed' : 'pointer',
            border: '1px solid var(--border)'
          }}
          onMouseEnter={e => { if (query.trim() && !loading) e.currentTarget.style.background = 'var(--accent-hover)'; }}
          onMouseLeave={e => { if (query.trim() && !loading) e.currentTarget.style.background = 'var(--accent)'; }}
        >
          ↑
        </button>
      </div>
      <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '8px', textAlign: 'center' }}>
        Enter to send · Shift+Enter for new line
      </div>
    </div>
  );
}
