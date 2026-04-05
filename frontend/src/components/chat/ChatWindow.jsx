import { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { chatAPI, exportAPI } from '../../api/client';

const TYPE_CONFIG = {
  excel: { label: 'SQL Mode', color: '#10B981', bg: 'rgba(16,185,129,0.1)', dot: '#10B981' },
  csv:   { label: 'SQL Mode', color: '#10B981', bg: 'rgba(16,185,129,0.1)', dot: '#10B981' },
  pdf:   { label: 'RAG Mode', color: '#F59E0B', bg: 'rgba(245,158,11,0.1)', dot: '#F59E0B' },
  text:  { label: 'RAG Mode', color: '#F59E0B', bg: 'rgba(245,158,11,0.1)', dot: '#F59E0B' },
};

const HINTS = {
  sql:    ['What is the monthly total?', 'Show me a bar chart of top 10 rows', 'Compare values across categories'],
  vector: ['Summarize this document', 'What does it say about...?', 'List the key points'],
};

export default function ChatWindow({ workspace }) {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasChart, setHasChart] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    setMessages([]);
    setSessionId(null);
    setHasChart(false);
    if (workspace?.workspace_id) loadHistory(workspace.workspace_id);
  }, [workspace.workspace_id]);

  const loadHistory = async (id) => {
    try {
      const res = await chatAPI.getHistory(id);
      if (res.data?.length > 0) {
        const latest = res.data[0];
        setSessionId(latest.session_id);
        const msgs = latest.messages.map((m, i) => ({ role: m.role, content: m.content, metadata: m.metadata, id: `h${i}` }));
        setMessages(msgs);
        if (msgs.some(m => m.metadata?.has_chart)) setHasChart(true);
      }
    } catch {}
  };

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const sendMessage = async (query) => {
    setMessages(prev => [...prev, { role: 'user', content: query, id: Date.now() }]);
    setLoading(true);
    try {
      const res = await chatAPI.sendMessage(workspace.workspace_id, query, sessionId);
      const { answer, metadata, session_id } = res.data;
      setSessionId(session_id);
      if (metadata?.has_chart) setHasChart(true);
      setMessages(prev => [...prev, { role: 'assistant', content: answer, metadata, id: Date.now() + 1 }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + (err.response?.data?.detail || 'Something went wrong'), id: Date.now() + 1 }]);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (type = 'excel') => {
    if (!sessionId) return;
    try {
      const res = type === 'excel'
        ? await exportAPI.exportExcel(sessionId, workspace.workspace_id)
        : await exportAPI.exportPowerBI(sessionId, workspace.workspace_id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a'); a.href = url;
      a.download = `${type}_export_${Date.now()}.xlsx`; a.click();
      window.URL.revokeObjectURL(url);
    } catch {}
  };

  const tc = TYPE_CONFIG[workspace.file_type] || TYPE_CONFIG.text;
  const isSql = ['excel', 'csv'].includes(workspace.file_type);
  const hints = isSql ? HINTS.sql : HINTS.vector;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg-base)' }}>
      {/* Header */}
      <div style={{
        padding: '14px 24px', borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'var(--bg-surface)', flexShrink: 0
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: tc.bg, padding: '4px 10px', borderRadius: '20px', border: `1px solid ${tc.color}22`, flexShrink: 0 }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: tc.dot, display: 'inline-block' }} />
            <span style={{ fontSize: '11px', fontWeight: 600, color: tc.color, letterSpacing: '0.03em' }}>{tc.label}</span>
          </div>
          <span style={{ fontWeight: 500, fontSize: '14px', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{workspace.filename}</span>
        </div>

        {hasChart && sessionId && (
          <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
            <button onClick={() => handleExport('excel')} style={{ padding: '7px 14px', background: 'var(--gradient)', color: '#fff', borderRadius: 'var(--radius-md)', fontSize: '12px', fontWeight: 600, cursor: 'pointer', boxShadow: '0 2px 8px rgba(99,102,241,0.3)', transition: 'opacity 0.2s' }}
              onMouseEnter={e => e.currentTarget.style.opacity = '0.85'}
              onMouseLeave={e => e.currentTarget.style.opacity = '1'}>
              ↓ Export
            </button>
            <button onClick={() => handleExport('powerbi')} style={{ padding: '7px 14px', background: 'var(--bg-elevated)', color: 'var(--text-secondary)', borderRadius: 'var(--radius-md)', fontSize: '12px', fontWeight: 500, cursor: 'pointer', border: '1px solid var(--border)', transition: 'all 0.2s' }}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-card-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'var(--bg-elevated)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}>
              Power BI
            </button>
          </div>
        )}
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 24px 8px' }}>
        {messages.length === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', textAlign: 'center', paddingBottom: '60px' }}>
            <div style={{ width: '56px', height: '56px', background: 'var(--gradient)', borderRadius: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', marginBottom: '20px', boxShadow: '0 8px 24px rgba(99,102,241,0.25)' }}>✦</div>
            <h3 style={{ fontSize: '17px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
              Ask anything about <span style={{ background: 'var(--gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{workspace.filename}</span>
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '24px' }}>
              {isSql ? 'Natural language → SQL → insights + charts' : 'Semantic search across your document'}
            </p>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center', maxWidth: '500px' }}>
              {hints.map(hint => (
                <button key={hint} onClick={() => sendMessage(hint)} style={{ padding: '7px 14px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '20px', color: 'var(--text-secondary)', fontSize: '12px', cursor: 'pointer', transition: 'all 0.15s' }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-active)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}>
                  {hint}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => <ChatMessage key={msg.id} message={msg} />)}

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '12px 0 4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '10px 16px' }}>
              {[0, 1, 2].map(i => (
                <div key={i} style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent)', animation: `pulse-dot 1.2s ease-in-out ${i * 0.2}s infinite` }} />
              ))}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={sendMessage} loading={loading} />
    </div>
  );
}
