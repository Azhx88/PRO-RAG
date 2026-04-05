import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const client = axios.create({ baseURL: API_BASE });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default client;

export const authAPI = {
  login: (email, password) => client.post('/auth/login', { email, password }),
  register: (email, password) => client.post('/auth/register', { email, password }),
};

export const filesAPI = {
  upload: (formData) => client.post('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  list: () => client.get('/files/list'),
};

export const chatAPI = {
  sendMessage: (workspaceId, query, sessionId = null) =>
    client.post('/chat/message', { workspace_id: workspaceId, query, session_id: sessionId }),
  getHistory: (workspaceId) => client.get(`/chat/history/${workspaceId}`),
};

export const exportAPI = {
  exportExcel: (sessionId, workspaceId) =>
    client.post('/export/excel', { session_id: sessionId, workspace_id: workspaceId }, {
      responseType: 'blob'
    }),
  exportPowerBI: (sessionId, workspaceId) =>
    client.post('/export/powerbi', { session_id: sessionId, workspace_id: workspaceId }, {
      responseType: 'blob'
    }),
};
