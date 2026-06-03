const API_BASE = 'http://127.0.0.1:8000/api';

export const api = {
  getAuthToken: () => {
    return localStorage.getItem('access_token');
  },

  chatStream: async (query, role = 'faq', conversation_id = null) => {
    const token = api.getAuthToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ query, role, conversation_id })
    });
  },
  
  getDbStats: async () => {
    const res = await fetch(`${API_BASE}/admin/stats`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminLogs: async () => {
    const res = await fetch(`${API_BASE}/admin/logs`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminUsers: async () => {
    const res = await fetch(`${API_BASE}/admin/users`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminData: async () => {
    const res = await fetch(`${API_BASE}/admin/data`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminChunks: async () => {
    const res = await fetch(`${API_BASE}/admin/chunks`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  runCrawler: async () => {
    return fetch(`${API_BASE}/admin/ingest/crawl`, {
      method: 'POST'
    });
  },

  runIngestion: async () => {
    return fetch(`${API_BASE}/admin/ingest/process`, {
      method: 'POST'
    });
  },

  getEvalResults: async () => {
    const res = await fetch(`${API_BASE}/admin/eval`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getDbTables: async () => {
    const res = await fetch(`${API_BASE}/admin/db/tables`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getTableData: async (tableName, limit = 50, offset = 0) => {
    const res = await fetch(`${API_BASE}/admin/db/table/${tableName}?limit=${limit}&offset=${offset}`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  deleteTableData: async (tableName, ids) => {
    const res = await fetch(`${API_BASE}/admin/db/table/${tableName}/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids })
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  deleteAllTableData: async (tableName) => {
    const res = await fetch(`${API_BASE}/admin/db/table/${tableName}/delete_all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getConversations: async () => {
    const token = api.getAuthToken();
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    
    const res = await fetch(`${API_BASE}/conversations`, { headers });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getConversationMessages: async (id) => {
    const token = api.getAuthToken();
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    
    const res = await fetch(`${API_BASE}/conversations/${id}/messages`, { headers });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  }
};
