const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api';

export const api = {
  getAuthToken: () => {
    return localStorage.getItem('access_token');
  },

  chatStream: async (query, conversation_id = null) => {
    const token = api.getAuthToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ query, conversation_id })
    });
  },
  
  getDbStats: async () => {
    const res = await fetch(`${API_BASE}/admin/stats`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminLogs: async (intent = null) => {
    let url = `${API_BASE}/admin/logs`;
    if (intent) {
      url += `?intent=${encodeURIComponent(intent)}`;
    }
    const res = await fetch(url);
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

  runAgentCrawler: async () => {
    return fetch(`${API_BASE}/admin/ingest/crawl/agent`, {
      method: 'POST'
    });
  },

  runIngestion: async () => {
    return fetch(`${API_BASE}/admin/ingest/process`, {
      method: 'POST'
    });
  },

  runPlatformIngestion: async () => {
    return fetch(`${API_BASE}/admin/ingest/process/platform`, {
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

  getTableData: async (tableName, limit = 50, offset = 0, filters = {}) => {
    let url = `${API_BASE}/admin/db/table/${tableName}?limit=${limit}&offset=${offset}`;
    if (filters.sort_by) url += `&sort_by=${encodeURIComponent(filters.sort_by)}`;
    if (filters.sort_order) url += `&sort_order=${encodeURIComponent(filters.sort_order)}`;
    if (filters.start_date) url += `&start_date=${encodeURIComponent(filters.start_date)}`;
    if (filters.end_date) url += `&end_date=${encodeURIComponent(filters.end_date)}`;
    if (filters.level) url += `&level=${encodeURIComponent(filters.level)}`;
    if (filters.error_type) url += `&error_type=${encodeURIComponent(filters.error_type)}`;
    
    const res = await fetch(url);
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
  },

  testPipeline: async (query) => {
    const res = await fetch(`${API_BASE}/admin/pipeline/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  }
};
