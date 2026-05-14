"""仪表盘相关Pydantic schemas"""
from typing import List, Optional

from pydantic import BaseModel


class OverviewData(BaseModel):
    """仪表盘概览数据（KPI卡片）"""
    total_transports: int             # 总运输次数
    today_transports: int             # 今日运输次数
    pending_alerts: int               # 待处理预警数
    severe_alerts: int                # 严重预警数
    anomaly_rate: float               # 异常率（有预警记录 / 总记录）
    avg_duration_minutes: int         # 平均运输时长（分钟）
    total_vehicles: int               # 在册车辆数
    active_vehicles: int              # 活跃车辆数


class AlertTrendItem(BaseModel):
    """预警趋势单日数据"""
    date: str                         # 日期（YYYY-MM-DD）
    total: int                        # 当日预警总数
    weight_count: int = 0             # 重量异常数
    time_count: int = 0               # 时间异常数
    seal_count: int = 0               # 铅封异常数
    severe_count: int = 0             # 严重预警数（可选，兼容旧版）


class TopRiskVehicle(BaseModel):
    """高风险车辆信息（兼容两种统计模式）"""
    plate_number: str
    total_alerts: int = 0             # 累计预警次数
    severe_count: int = 0             # 严重预警次数
    last_alert_time: Optional[str] = None  # 最近预警时间

    # 扩展字段（详细模式）
    vehicle_id: Optional[int] = None
    driver_name: Optional[str] = None
    transport_count: Optional[int] = None
    anomaly_rate: Optional[float] = None
    risk_score: Optional[float] = None


class WeightDistributionItem(BaseModel):
    """重量偏差分布区间"""
    range_min: float                  # 区间下界（‰）
    range_max: float                  # 区间上界（‰）
    count: int                        # 落在此区间的记录数
    range_label: Optional[str] = None  # 区间标签（可选）


class AlertTrendResponse(BaseModel):
    """预警趋势响应"""
    period: str                       # 统计周期（"day" / "week" / "month"）
    items: List[AlertTrendItem]


class TopRiskVehiclesResponse(BaseModel):
    """高风险车辆TOP榜响应"""
    items: List[TopRiskVehicle]


class WeightDistributionResponse(BaseModel):
    """重量偏差分布响应"""
    items: List[WeightDistributionItem]
    mean_ratio: float                 # 均值
    std_ratio: float                  # 标准差
    threshold: float                  # 预警阈值（3‰）
