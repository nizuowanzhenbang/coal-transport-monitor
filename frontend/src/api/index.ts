import axios from 'axios';
import type {
  ApiResponse,
  PaginatedResponse,
  Vehicle,
  VehicleCreate,
  TransportListItem,
  TransportDetail,
  AlertRecord,
  AlertStats,
  OverviewData,
  AlertTrendItem,
  TopRiskVehicle,
  WeightDistItem,
  RecordStatus,
  AlertType,
  Severity,
  AlertStatus,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
});

// 请求拦截器：自动附加 JWT token
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
  login: (username: string, password: string): Promise<ApiResponse<{ access_token: string; token_type: string }>> => {
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
  list: (params?: {
    page?: number;
    page_size?: number;
    plate?: string;
    status?: string;
  }): Promise<ApiResponse<PaginatedResponse<Vehicle>>> => api.get('/vehicles', { params }),

  create: (data: VehicleCreate): Promise<ApiResponse<Vehicle>> => api.post('/vehicles', data),

  get: (id: number): Promise<ApiResponse<Vehicle>> => api.get(`/vehicles/${id}`),

  update: (id: number, data: Partial<VehicleCreate>): Promise<ApiResponse<Vehicle>> =>
    api.put(`/vehicles/${id}`, data),

  history: (plate: string, params?: { page?: number; page_size?: number }): Promise<ApiResponse<PaginatedResponse<TransportListItem>>> =>
    api.get(`/vehicles/${plate}/history`, { params }),
};

// ---- 运输记录 ----
export const transportApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    plate?: string;
    status?: RecordStatus;
    start_date?: string;
    end_date?: string;
  }): Promise<ApiResponse<PaginatedResponse<TransportListItem>>> => api.get('/transports', { params }),

  create: (data: unknown): Promise<ApiResponse<TransportDetail>> => api.post('/transports', data),

  get: (id: number): Promise<ApiResponse<TransportDetail>> => api.get(`/transports/${id}`),

  update: (id: number, data: unknown): Promise<ApiResponse<TransportDetail>> =>
    api.put(`/transports/${id}`, data),

  alerts: (id: number): Promise<ApiResponse<AlertRecord[]>> => api.get(`/transports/${id}/alerts`),
};

// ---- 预警 ----
export const alertApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    alert_type?: AlertType;
    severity?: Severity;
    status?: AlertStatus;
    plate?: string;
  }): Promise<ApiResponse<PaginatedResponse<AlertRecord>>> => api.get('/alerts', { params }),

  acknowledge: (id: number): Promise<ApiResponse<AlertRecord>> =>
    api.put(`/alerts/${id}/acknowledge`),

  resolve: (id: number, notes: string): Promise<ApiResponse<AlertRecord>> =>
    api.put(`/alerts/${id}/resolve`, { resolution_notes: notes }),

  dismiss: (id: number): Promise<ApiResponse<AlertRecord>> =>
    api.put(`/alerts/${id}/dismiss`),

  stats: (days?: number): Promise<ApiResponse<AlertStats>> =>
    api.get('/alerts/stats', { params: { days } }),
};

// ---- 仪表盘 ----
export const dashboardApi = {
  overview: (): Promise<ApiResponse<OverviewData>> => api.get('/dashboard/overview'),

  alertTrend: (days?: number): Promise<ApiResponse<AlertTrendItem[]>> =>
    api.get('/dashboard/alert-trend', { params: { days } }),

  topRiskVehicles: (limit?: number): Promise<ApiResponse<TopRiskVehicle[]>> =>
    api.get('/dashboard/top-risk-vehicles', { params: { limit } }),

  weightDistribution: (bins?: number): Promise<ApiResponse<WeightDistItem[]>> =>
    api.get('/dashboard/weight-distribution', { params: { bins } }),
};

// ---- 数据导出 ----
export const exportApi = {
  transports: (params?: {
    status?: RecordStatus;
    start_date?: string;
    end_date?: string;
    plate?: string;
  }): void => {
    const token = localStorage.getItem('token');
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    const url = `/api/export/transports${qs ? `?${qs}` : ''}`;
    // 通过隐藏 <a> 触发浏览器原生下载（携带 Authorization 头需用 fetch+blob）
    _downloadWithAuth(url, '运输记录.csv');
  },

  alerts: (params?: {
    severity?: Severity;
    alert_status?: AlertStatus;
    alert_type?: AlertType;
    start_date?: string;
    end_date?: string;
  }): void => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    const url = `/api/export/alerts${qs ? `?${qs}` : ''}`;
    _downloadWithAuth(url, '预警记录.csv');
  },
};

function _downloadWithAuth(url: string, filename: string) {
  const token = localStorage.getItem('token');
  fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
    .then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.blob();
    })
    .then((blob) => {
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
    })
    .catch(console.error);
}

export default api;
