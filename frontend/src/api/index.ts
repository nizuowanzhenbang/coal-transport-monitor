import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

// 请求拦截器：自动附加JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(err.response?.data || err);
  }
);

// ---- 认证 ----
export const authApi = {
  login: (username: string, password: string) => {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    return api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  me: () => api.get('/auth/me'),
};

// ---- 车辆 ----
export const vehicleApi = {
  list: (params?: Record<string, any>) => api.get('/vehicles', { params }),
  create: (data: any) => api.post('/vehicles', data),
  get: (id: number) => api.get(`/vehicles/${id}`),
  update: (id: number, data: any) => api.put(`/vehicles/${id}`, data),
  history: (plate: string, params?: any) => api.get(`/vehicles/${plate}/history`, { params }),
};

// ---- 运输记录 ----
export const transportApi = {
  list: (params?: Record<string, any>) => api.get('/transports', { params }),
  create: (data: any) => api.post('/transports', data),
  get: (id: number) => api.get(`/transports/${id}`),
  update: (id: number, data: any) => api.put(`/transports/${id}`, data),
  alerts: (id: number) => api.get(`/transports/${id}/alerts`),
};

// ---- 预警 ----
export const alertApi = {
  list: (params?: Record<string, any>) => api.get('/alerts', { params }),
  acknowledge: (id: number) => api.put(`/alerts/${id}/acknowledge`),
  resolve: (id: number, notes: string) => api.put(`/alerts/${id}/resolve`, { resolution_notes: notes }),
  dismiss: (id: number) => api.put(`/alerts/${id}/dismiss`),
  stats: (days?: number) => api.get('/alerts/stats', { params: { days } }),
};

// ---- 仪表盘 ----
export const dashboardApi = {
  overview: () => api.get('/dashboard/overview'),
  alertTrend: (days?: number) => api.get('/dashboard/alert-trend', { params: { days } }),
  topRiskVehicles: (limit?: number) => api.get('/dashboard/top-risk-vehicles', { params: { limit } }),
  weightDistribution: (bins?: number) => api.get('/dashboard/weight-distribution', { params: { bins } }),
};

export default api;
