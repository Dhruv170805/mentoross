// MentorOS – Axios API Client
// All requests go through this client. Auth token auto-injected.

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('access_token');
  }

  setToken(token) {
    this.token = token;
    if (token) localStorage.setItem('access_token', token);
    else localStorage.removeItem('access_token');
  }

  async request(method, path, data = null, params = null) {
    const url = new URL(this.baseURL + path);
    if (params) Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.append(k, v));

    const headers = { 'Content-Type': 'application/json' };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

    const opts = { method, headers };
    if (data) opts.body = JSON.stringify(data);

    const res = await fetch(url.toString(), opts);

    // Auto-refresh on 401
    if (res.status === 401) {
      const refreshed = await this._tryRefresh();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.token}`;
        const retry = await fetch(url.toString(), { ...opts, headers });
        return this._parse(retry);
      }
      this._logout();
      throw new Error('Session expired. Please log in again.');
    }

    return this._parse(res);
  }

  async _parse(res) {
    const text = await res.text();
    let json;
    try { json = JSON.parse(text); } catch { json = { detail: text }; }
    if (!res.ok) throw new Error(json?.detail || `HTTP ${res.status}`);
    return json;
  }

  async _tryRefresh() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return false;
    try {
      const res = await fetch(`${this.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      this.setToken(data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      return true;
    } catch { return false; }
  }

  _logout() {
    this.setToken(null);
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/';
  }

  get(path, params)    { return this.request('GET',    path, null, params); }
  post(path, data)     { return this.request('POST',   path, data); }
  put(path, data)      { return this.request('PUT',    path, data); }
  patch(path, data)    { return this.request('PATCH',  path, data); }
  delete(path)         { return this.request('DELETE', path); }
}

export const api = new ApiClient(API_URL);

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (email, name, password) => api.post('/auth/register', { email, name, password }),
  login:    (email, password)        => api.post('/auth/login',    { email, password }),
  refresh:  (refresh_token)          => api.post('/auth/refresh',  { refresh_token }),
  me:       ()                        => api.get('/auth/me'),
  updateMe: (data)                    => api.patch('/auth/me', data),
};

// ── Tasks ────────────────────────────────────────────────────────────────────
export const tasksApi = {
  list:   (params) => api.get('/tasks/', params),
  stats:  ()       => api.get('/tasks/stats'),
  create: (data)   => api.post('/tasks/', data),
  update: (id, d)  => api.put(`/tasks/${id}`, d),
  delete: (id)     => api.delete(`/tasks/${id}`),
};

// ── Notes ────────────────────────────────────────────────────────────────────
export const notesApi = {
  list:   (params) => api.get('/notes/', params),
  create: (data)   => api.post('/notes/', data),
  update: (id, d)  => api.patch(`/notes/${id}`, d),
  delete: (id)     => api.delete(`/notes/${id}`),
  search: (q)      => api.get('/notes/search', { q }),
};

// ── Roadmaps ─────────────────────────────────────────────────────────────────
export const roadmapsApi = {
  list:         ()           => api.get('/roadmaps/'),
  create:       (data)       => api.post('/roadmaps/', data),
  delete:       (id)         => api.delete(`/roadmaps/${id}`),
  addPhase:     (rmId, data) => api.post(`/roadmaps/${rmId}/phases`, data),
  deletePhase:  (phId)       => api.delete(`/roadmaps/phases/${phId}`),
  addTopic:     (phId, data) => api.post(`/roadmaps/phases/${phId}/topics`, data),
  updateTopic:  (tId, data)  => api.patch(`/roadmaps/topics/${tId}`, data),
  deleteTopic:  (tId)        => api.delete(`/roadmaps/topics/${tId}`),
};

// ── Resources ────────────────────────────────────────────────────────────────
export const resourcesApi = {
  list:   (params) => api.get('/resources/', params),
  tags:   ()       => api.get('/resources/tags'),
  create: (data)   => api.post('/resources/', data),
  update: (id, d)  => api.patch(`/resources/${id}`, d),
  delete: (id)     => api.delete(`/resources/${id}`),
};

// ── Plans ────────────────────────────────────────────────────────────────────
export const plansApi = {
  today:    ()     => api.get('/plans/today'),
  save:     (data) => api.post('/plans/', data),
  generate: ()     => api.post('/plans/generate'),
};

// ── AI Review ────────────────────────────────────────────────────────────────
export const reviewApi = {
  run:     () => api.post('/reviewer/evaluate'),
  history: () => api.get('/reviewer/history'),
};

// ── AI Teacher ───────────────────────────────────────────────────────────────
export const teacherApi = {
  explain: (topic, level = 'intermediate') => api.post('/teacher/explain', { topic, level }),
};

// ── Analytics ────────────────────────────────────────────────────────────────
export const analyticsApi = {
  overview: () => api.get('/analytics/overview'),
};
