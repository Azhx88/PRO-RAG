import { useState, useRef } from 'react';

export default function ChatInput({ onSend, loading }) {
  const [query, setQuery] = useState('');
  const textareaRef = useRef();

  const handleSend = () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setQuery('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const handleInput = (e) => {
    setQuery(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
  };

  const canSend = !!query.trim() && !loading;

  return (
    <div style={{ padding: '12px 20px 16px', background: 'var(--bg-surface)', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
      <div style={{
        display: 'flex', gap: '10px', alignItems: 'flex-end',
        background: 'var(--bg-card)', borderRadius: '16px',
        border: '1px solid var(--border)', padding: '10px 14px',
        transition: 'border-color 0.2s, box-shadow 0.2s',
        boxShadow: 'none'
      }}
        onFocus={() => {}}
      >
        <textarea
          ref={textareaRef}
          value={query}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about this file..."
          rows={1}
          style={{
            flex: 1, background: 'transparent', border: 'none',
            color: 'var(--text-primary)', fontSize: '14px', lineHeight: 1.6,
            resize: 'none', outline: 'none', maxHeight: '150px',
            overflowY: 'auto', fontFamily: 'inherit', paddingTop: '2px'
          }}
        />
        <button
          onClick={handleSend}
          disabled={!canSend}
          style={{
            width: '34px', height: '34px', flexShrink: 0, borderRadius: '10px',
            background: canSend ? 'linear-gradient(135deg, #6366F1, #8B5CF6)' : 'var(--bg-elevated)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s', cursor: canSend ? 'pointer' : 'not-allowed',
            border: canSend ? 'none' : '1px solid var(--border)',
            boxShadow: canSend ? '0 2px 10px rgba(99,102,241,0.35)' : 'none',
            fontSize: '14px', color: canSend ? '#fff' : 'var(--text-muted)'
          }}
          onMouseEnter={e => { if (canSend) { e.currentTarget.style.transform = 'scale(1.05)'; e.currentTarget.style.boxShadow = '0 4px 16px rgba(99,102,241,0.45)'; } }}
          onMouseLeave={e => { if (canSend) { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 2px 10px rgba(99,102,241,0.35)'; } }}
        >
          ↑
        </button>
      </div>
      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', textAlign: 'center', letterSpacing: '0.02em' }}>
        Enter to send · Shift+Enter for new line
      </div>
    </div>
  );
}
