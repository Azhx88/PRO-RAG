import { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { chatAPI, exportAPI } from '../../api/client';

export default function ChatWindow({ workspace }) {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasChart, setHasChart] = useState(false);
  const messagesEndRef = useRef(null);
  
  // Reset and load history on workspace change
  useEffect(() => {
    setMessages([]);
    setSessionId(null);
    setHasChart(false);
    
    if (workspace?.workspace_id) {
      loadHistory(workspace.workspace_id);
    }
  }, [workspace.workspace_id]);

  const loadHistory = async (id) => {
    try {
      setLoading(true);
      const res = await chatAPI.getHistory(id);
      if (res.data && res.data.length > 0) {
        // Load the most recent session
        const latestSession = res.data[0];
        setSessionId(latestSession.session_id);
        
        // Map messages to UI format
        const historyMsgs = latestSession.messages.map((m, i) => ({
          role: m.role,
          content: m.content,
          metadata: m.metadata,
          id: `hist-${i}`
        }));
        
        setMessages(historyMsgs);
        if (historyMsgs.some(m => m.metadata?.has_chart || m.metadata?.chart_path)) {
          setHasChart(true);
        }
      }
    } catch (err) {
      console.error('Failed to load history', err);
    } finally {
      setLoading(false);
    }
  };

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (query) => {
    const userMsg = { role: 'user', content: query, id: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await chatAPI.sendMessage(workspace.workspace_id, query, sessionId);
      const { answer, metadata, session_id } = res.data;
      setSessionId(session_id);

      if (metadata?.has_chart) setHasChart(true);

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: answer,
        metadata: metadata,
        id: Date.now() + 1
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: ' + (err.response?.data?.detail || 'Something went wrong'),
        id: Date.now() + 1
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!sessionId) return;
    try {
      const res = await exportAPI.exportExcel(sessionId, workspace.workspace_id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `dashboard_export_${Date.now()}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export Excel failed', err);
    }
  };

  const handleExportPowerBI = async () => {
    if (!sessionId) return;
    try {
      const res = await exportAPI.exportPowerBI(sessionId, workspace.workspace_id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `powerbi_export_${Date.now()}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export PowerBI failed', err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg-base)' }}>
      {/* Top bar */}
      <div style={{
        padding: '16px 24px', borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: '#1A1814'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{
            fontSize: '11px', fontWeight: 700,
            color: workspace.file_type === 'excel' || workspace.file_type === 'csv' ? '#4CAF7D' : '#E8A84A',
            background: workspace.file_type === 'excel' || workspace.file_type === 'csv' ? '#4CAF7D20' : '#E8A84A20',
            padding: '3px 8px', borderRadius: '5px'
          }}>
            {workspace.file_type?.toUpperCase()}
          </span>
          <span style={{ fontWeight: 500, fontSize: '15px' }}>{workspace.filename}</span>
          <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
            {workspace.file_type === 'excel' || workspace.file_type === 'csv' ? 'SQL Mode' : 'RAG Mode'}
          </span>
        </div>

        {hasChart && sessionId && (
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handleExport}
              style={{
                padding: '8px 16px', background: 'var(--accent)',
                color: '#fff', borderRadius: 'var(--radius-md)',
                fontSize: '13px', fontWeight: 600, border: 'none', cursor: 'pointer',
                transition: 'background 0.2s'
              }}
              onMouseEnter={e => e.target.style.background = 'var(--accent-hover)'}
              onMouseLeave={e => e.target.style.background = 'var(--accent)'}
            >
              Export Dashboard
            </button>
            <button
              onClick={handleExportPowerBI}
              style={{
                padding: '8px 16px', background: '#334155',
                color: '#fff', borderRadius: 'var(--radius-md)',
                fontSize: '13px', fontWeight: 600, border: '1px solid #475569', cursor: 'pointer',
                transition: 'background 0.2s'
              }}
              onMouseEnter={e => e.target.style.background = '#475569'}
              onMouseLeave={e => e.target.style.background = '#334155'}
            >
              Data (Power BI)
            </button>
          </div>
        )}
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', paddingTop: '60px', color: 'var(--text-tertiary)' }}>
            <p style={{ fontSize: '15px' }}>Ask anything about <strong style={{ color: 'var(--text-secondary)' }}>{workspace.filename}</strong></p>
            <p style={{ fontSize: '13px', marginTop: '8px' }}>
              {workspace.file_type === 'excel' || workspace.file_type === 'csv'
                ? 'Try: "What is the monthly total?" or "Show me a bar chart of sales by region"'
                : 'Try: "Summarize this document" or "What does it say about X?"'}
            </p>
          </div>
        )}

        {messages.map(msg => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {loading && (
          <div style={{ display: 'flex', gap: '6px', padding: '16px 0', alignItems: 'center' }}>
            {[0, 1, 2].map(i => (
              <div key={i} style={{
                width: '8px', height: '8px', background: 'var(--accent)',
                borderRadius: '50%', opacity: 0.6,
                animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`
              }} />
            ))}
            <style>{`@keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }`}</style>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={sendMessage} loading={loading} />
    </div>
  );
}
