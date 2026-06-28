export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api/v1';

export const api = {
    _fetch: async (url, options = {}) => {
    const token = api.getAuthToken();
    const headers = { ...options.headers };
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }
    if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }
    return fetch(url, { ...options, headers });
  },

  getAuthToken: () => {
    return localStorage.getItem('access_token');
  },

  chatStream: async (query, conversation_id = null, imageBase64 = null, isDeepSearch = false, displayQuery = null, persona = 'customer', context = {}) => {
    const token = api.getAuthToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const body = { query, conversation_id, deep_search: isDeepSearch, display_query: displayQuery, persona };
    if (context.lat !== undefined && context.lat !== null) body.lat = context.lat;
    if (context.lng !== undefined && context.lng !== null) body.lng = context.lng;
    if (context.address) body.address = context.address;
    if (context.budget_vnd !== undefined && context.budget_vnd !== null) body.budget_vnd = context.budget_vnd;
    if (imageBase64) {
      body.image_base64 = imageBase64;
    }

    return api._fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    });
  },

  estimateRide: async (payload) => {
    const res = await api._fetch(`${API_BASE}/booking/estimate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  createRideBooking: async (payload) => {
    const res = await api._fetch(`${API_BASE}/booking`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  previewRide: async (pickup, dropoff, serviceType = 'xanh_car') => {
    const params = new URLSearchParams({ pickup, dropoff, service_type: serviceType });
    const res = await api._fetch(`${API_BASE}/booking/preview?${params.toString()}`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getNotifications: async () => {
    const res = await api._fetch(`${API_BASE}/notifications`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  markNotificationRead: async (id) => {
    const res = await api._fetch(`${API_BASE}/notifications/${id}/read`, { method: 'POST' });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  markAllNotificationsRead: async () => {
    const res = await api._fetch(`${API_BASE}/notifications/read-all`, { method: 'POST' });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getDbStats: async () => {
    const res = await api._fetch(`${API_BASE}/admin/stats`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getSystemHealth: async () => {
    const res = await api._fetch(`${API_BASE}/admin/health`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminLogs: async (intent = null) => {
    let url = `${API_BASE}/admin/logs`;
    if (intent) {
      url += `?intent=${encodeURIComponent(intent)}`;
    }
    const res = await api._fetch(url);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getRagLogs: async (skip = 0, limit = 50, date = '') => {
    let url = `${API_BASE}/admin/logs/rag?skip=${skip}&limit=${limit}`;
    if (date) url += `&date=${date}`;
    const res = await api._fetch(url);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getFoodLogs: async (skip = 0, limit = 50, date = '') => {
    let url = `${API_BASE}/admin/logs/food?skip=${skip}&limit=${limit}`;
    if (date) url += `&date=${date}`;
    const res = await api._fetch(url);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getBasicLogs: async (skip = 0, limit = 50, intent = '', date = '') => {
    let url = `${API_BASE}/admin/logs/basic?skip=${skip}&limit=${limit}`;
    if (intent && intent !== 'all') {
      url += `&intent=${encodeURIComponent(intent)}`;
    }
    if (date) url += `&date=${date}`;
    const res = await api._fetch(url);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminUsers: async () => {
    const res = await api._fetch(`${API_BASE}/admin/users`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminData: async () => {
    const res = await api._fetch(`${API_BASE}/admin/data`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getFoodTraces: async (skip = 0, limit = 50) => {
    const res = await api._fetch(`${API_BASE}/admin/food-traces?skip=${skip}&limit=${limit}`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminChunks: async () => {
    const res = await api._fetch(`${API_BASE}/admin/chunks`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  runCrawler: async (maxUrls = 0) => {
    const params = new URLSearchParams();
    params.set('max_urls', String(Math.max(0, Number(maxUrls) || 0)));
    return api._fetch(`${API_BASE}/admin/ingest/crawl?${params.toString()}`, {
      method: 'POST'
    });
  },

  runVLMProcessor: async () => {
    return api._fetch(`${API_BASE}/admin/ingest/process/vlm`, {
      method: 'POST'
    });
  },

  runIngestion: async () => {
    return api._fetch(`${API_BASE}/admin/ingest/process`, {
      method: 'POST'
    });
  },

  runPlatformIngestion: async () => {
    return api._fetch(`${API_BASE}/admin/ingest/process/platform`, {
      method: 'POST'
    });
  },

  getCrawlSources: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.source_profile) params.set('source_profile', filters.source_profile);
    if (filters.category) params.set('category', filters.category);
    if (filters.enabled !== undefined && filters.enabled !== '') params.set('enabled', filters.enabled);
    if (filters.keyword) params.set('keyword', filters.keyword);
    const qs = params.toString();
    const res = await api._fetch(`${API_BASE}/admin/crawl-sources${qs ? `?${qs}` : ''}`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getCrawlSourceStats: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.source_profile) params.set('source_profile', filters.source_profile);
    if (filters.category) params.set('category', filters.category);
    if (filters.enabled !== undefined && filters.enabled !== '') params.set('enabled', filters.enabled);
    if (filters.keyword) params.set('keyword', filters.keyword);
    const qs = params.toString();
    const res = await api._fetch(`${API_BASE}/admin/crawl-sources/stats${qs ? `?${qs}` : ''}`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  createCrawlSource: async (payload) => {
    const res = await api._fetch(`${API_BASE}/admin/crawl-sources`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  updateCrawlSource: async (id, payload) => {
    const res = await api._fetch(`${API_BASE}/admin/crawl-sources/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  updateAllCrawlSourcesStatus: async (enabled) => {
    const res = await api._fetch(`${API_BASE}/admin/crawl-sources/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  deleteCrawlSource: async (id) => {
    const res = await api._fetch(`${API_BASE}/admin/crawl-sources/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  bootstrapCrawlSources: async () => {
    const res = await api._fetch(`${API_BASE}/admin/crawl-sources/bootstrap`, { method: 'POST' });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  syncCrawlSources: async () => {
    const res = await api._fetch(`${API_BASE}/admin/crawl-sources/sync`, { method: 'POST' });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  clearAllKnowledge: async () => {
    const res = await api._fetch(`${API_BASE}/admin/knowledge/clear`, { method: 'POST' });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  ingestAllKnowledge: async () => {
    const res = await api._fetch(`${API_BASE}/admin/knowledge/ingest-all`, { method: 'POST' });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  importFoodCatalog: async (payload = {}) => {
    const res = await api._fetch(`${API_BASE}/admin/food-catalog/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  testFoodRecommendation: async (payload) => {
    const res = await api._fetch(`${API_BASE}/admin/food-catalog/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  logFoodInteraction: async (payload) => {
    const res = await api._fetch(`${API_BASE}/food/interactions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getFoodInteractionStats: async (limit = 20) => {
    const res = await api._fetch(`${API_BASE}/food/interactions/stats?limit=${limit}`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  geocodeFoodAddress: async (address) => {
    const params = new URLSearchParams({ address });
    const res = await api._fetch(`${API_BASE}/food/geocode?${params.toString()}`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  saveFoodLocation: async (payload) => {
    const res = await api._fetch(`${API_BASE}/food/locations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getEvalResults: async () => {
    const res = await api._fetch(`${API_BASE}/admin/eval`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getEvalRuns: async (limit = 20) => {
    const res = await api._fetch(`${API_BASE}/admin/eval/runs?limit=${limit}`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getDbTables: async () => {
    const res = await api._fetch(`${API_BASE}/admin/db/tables`);
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
    if (filters.keyword) url += `&keyword=${encodeURIComponent(filters.keyword)}`;
    if (filters.search_columns) url += `&search_columns=${encodeURIComponent(filters.search_columns)}`;
    
    const res = await api._fetch(url);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  deleteTableData: async (tableName, ids) => {
    const res = await api._fetch(`${API_BASE}/admin/db/table/${tableName}/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids })
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  deleteAllTableData: async (tableName) => {
    const res = await api._fetch(`${API_BASE}/admin/db/table/${tableName}/delete_all`, {
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
    
    const res = await api._fetch(`${API_BASE}/conversations`, { headers });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getConversationMessages: async (id) => {
    const token = api.getAuthToken();
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    
    const res = await api._fetch(`${API_BASE}/conversations/${id}/messages`, { headers });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  testPipeline: async (query) => {
    const res = await api._fetch(`${API_BASE}/admin/pipeline/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  adminLogin: async (username, password) => {
    const res = await api._fetch(`${API_BASE}/auth/admin-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  submitReview: async (payload) => {
    const token = api.getAuthToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await api._fetch(`${API_BASE}/reviews`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminReviews: async (filters = {}) => {
    const token = api.getAuthToken();
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const params = new URLSearchParams();
    if (filters.status) params.set('status', filters.status);
    if (filters.rating) params.set('rating', filters.rating);
    if (filters.keyword) params.set('keyword', filters.keyword);
    if (filters.limit) params.set('limit', filters.limit);
    if (filters.offset) params.set('offset', filters.offset);

    const qs = params.toString();
    const res = await api._fetch(`${API_BASE}/admin/reviews${qs ? `?${qs}` : ''}`, { headers });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminReviewDetail: async (id) => {
    const token = api.getAuthToken();
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await api._fetch(`${API_BASE}/admin/reviews/${id}`, { headers });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  updateAdminReviewStatus: async (id, payload) => {
    const token = api.getAuthToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await api._fetch(`${API_BASE}/admin/reviews/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  getAdminNotifications: async (status = 'all') => {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    const res = await api._fetch(`${API_BASE}/admin/notifications?${params.toString()}`);
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  createAdminNotification: async (payload) => {
    const res = await api._fetch(`${API_BASE}/admin/notifications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  updateAdminNotification: async (id, payload) => {
    const res = await api._fetch(`${API_BASE}/admin/notifications/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  updateAdminNotificationStatus: async (id, status) => {
    const res = await api._fetch(`${API_BASE}/admin/notifications/${id}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  },

  archiveAdminNotification: async (id) => {
    const res = await api._fetch(`${API_BASE}/admin/notifications/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('API Error');
    return res.json();
  }
};
