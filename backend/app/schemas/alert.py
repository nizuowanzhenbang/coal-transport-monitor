"""预警相关Pydantic schemas"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.alert import AlertType, Severity, AlertStatus


class AlertResponse(BaseModel):
    """预警记录响应"""
    id: int
    transport_id: int
    alert_type: AlertType
    severity: Severity
    description: str
    threshold_value: Optional[float]
    actual_value: Optional[float]
    status: AlertStatus
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime

    # 关联运输信息（可选）
    vehicle_plate: Optional[str] = None
    departure_port: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AlertAcknowledgeRequest(BaseModel):
    """确认预警请求体"""
    notes: Optional[str] = None


class AlertResolveRequest(BaseModel):
    """处理/解决预警请求体"""
    resolution_notes: str  # 处理备注（必填）


class AlertFilterParams(BaseModel):
    """预警查询筛选参数"""
    page: int = 1
    size: int = 20
    alert_type: Optional[AlertType] = None
    severity: Optional[Severity] = None
    status: Optional[AlertStatus] = None
    transport_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class AlertStats(BaseModel):
    """预警统计数据"""
    total: int                        # 总预警数
    pending: int                      # 待处理数
    acknowledged: int                 # 已确认数
    resolved: int                     # 已解决数
    dismissed: int                    # 已忽略数
    weight_shortage_count: int        # 重量亏损预警数
    weight_overage_count: int         # 重量盈余预警数
    time_excessive_count: int         # 超时预警数
    seal_mismatch_count: int          # 铅封不匹配预警数
    seal_damaged_count: int           # 铅封损坏预警数
    general_count: int                # 一般预警数
    severe_count: int                 # 严重预警数
