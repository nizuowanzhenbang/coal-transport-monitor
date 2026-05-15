/** 共享 TypeScript 类型定义 */

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ---- 车辆 ----
export type VehicleStatus = 'ACTIVE' | 'INACTIVE';

export interface Vehicle {
  id: number;
  plate_number: string;
  tare_weight: number;
  driver_name: string;
  driver_phone: string;
  status: VehicleStatus;
  created_at: string;
  updated_at: string;
}

export interface VehicleCreate {
  plate_number: string;
  driver_name: string;
  driver_phone?: string;
  tare_weight: number;
}

// ---- 运输记录 ----
export type RecordStatus = 'NORMAL' | 'ALERT' | 'SEVERE';

export interface TransportListItem {
  id: number;
  vehicle_id: number;
  plate_number: string;
  departure_port: string | null;
  departure_time: string | null;
  arrival_time: string | null;
  departure_net_weight: number | null;
  arrival_net_weight: number | null;
  weight_diff_ratio: number | null;
  transport_duration: number | null;
  status: RecordStatus;
  alert_count: number;
}

export interface TransportDetail extends TransportListItem {
  departure_weight: number | null;
  arrival_weight: number | null;
  weight_diff: number | null;
  departure_seal_id: number | null;
  arrival_seal_id: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  alerts: AlertRecord[];
}

// ---- 预警 ----
export type AlertType =
  | 'WEIGHT_SHORTAGE'
  | 'WEIGHT_OVERAGE'
  | 'TIME_EXCESSIVE'
  | 'SEAL_MISMATCH'
  | 'SEAL_DAMAGED';

export type Severity = 'GENERAL' | 'SEVERE';
export type AlertStatus = 'PENDING' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';

export interface AlertRecord {
  id: number;
  transport_id: number;
  alert_type: AlertType;
  severity: Severity;
  description: string;
  threshold_value: number | null;
  actual_value: number | null;
  status: AlertStatus;
  resolved_by: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
  created_at: string;
  // 附加字段（列表接口注入）
  plate_number?: string;
  departure_port?: string;
  departure_time?: string;
}

export interface AlertStats {
  total: number;
  days: number;
  by_type: Partial<Record<AlertType, number>>;
  by_severity: Partial<Record<Severity, number>>;
  by_status: Partial<Record<AlertStatus, number>>;
}

// ---- 仪表盘 ----
export interface OverviewData {
  total_transports: number;
  today_transports: number;
  pending_alerts: number;
  severe_alerts: number;
  anomaly_rate: number;
  avg_duration_minutes: number;
  total_vehicles: number;
  active_vehicles: number;
}

export interface AlertTrendItem {
  date: string;
  total: number;
  weight_count: number;
  time_count: number;
  seal_count: number;
}

export interface TopRiskVehicle {
  plate_number: string;
  total_alerts: number;
  severe_count: number;
  last_alert_time: string | null;
}

export interface WeightDistItem {
  range_min: number;
  range_max: number;
  count: number;
}

// ---- WebSocket 消息 ----
export interface WsNewAlert {
  type: 'new_alert';
  data: {
    id: number;
    transport_id: number;
    alert_type: AlertType;
    severity: Severity;
    description: string;
    created_at: string;
  };
}

export interface WsPing {
  type: 'ping' | 'pong';
}

export type WsMessage = WsNewAlert | WsPing;
