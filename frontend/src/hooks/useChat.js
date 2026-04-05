import { useState, useCallback } from 'react';
import { chatAPI } from '../api/client';

export function useChat(workspaceId) {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);

  const sendMessage = useCallback(async (query) => {
    setMessages(prev => [...prev, { role: 'user', content: query, id: Date.now() }]);
    setLoading(true);
    try {
      const res = await chatAPI.sendMessage(workspaceId, query, sessionId);
      const { answer, metadata, session_id } = res.data;
      setSessionId(session_id);
      setMessages(prev => [...prev, { role: 'assistant', content: answer, metadata, id: Date.now() + 1 }]);
      return res.data;
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: ' + (err.response?.data?.detail || 'Something went wrong'),
        id: Date.now() + 1
      }]);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, sessionId]);

  const reset = useCallback(() => {
    setMessages([]);
    setSessionId(null);
  }, []);

  return { messages, sessionId, loading, sendMessage, reset };
}
