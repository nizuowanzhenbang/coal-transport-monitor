"""运输记录相关Pydantic schemas"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.transport import RecordStatus
from app.schemas.seal import SealRecordResponse


class TransportRecordCreate(BaseModel):
    """创建运输记录请求体（同时接受铅封二维码用于自动创建铅封记录）"""
    vehicle_id: int
    departure_port: str
    departure_weight: float           # 出港毛重
    departure_net_weight: float       # 出港净重
    departure_time: datetime
    departure_seal_qr: Optional[str] = None   # 出港铅封二维码
    departure_seal_valid: bool = True         # 出港铅封是否有效

    arrival_weight: float             # 进厂毛重
    arrival_net_weight: float         # 进厂净重
    arrival_time: datetime
    arrival_seal_qr: Optional[str] = None    # 进厂铅封二维码
    arrival_seal_valid: bool = True          # 进厂铅封是否有效

    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_times(self) -> "TransportRecordCreate":
        # 到达时间必须晚于出发时间
        if self.arrival_time <= self.departure_time:
            raise ValueError("到达时间必须晚于出发时间")
        return self


class TransportRecordUpdate(BaseModel):
    """更新运输记录请求体"""
    notes: Optional[str] = None
    arrival_weight: Optional[float] = None
    arrival_net_weight: Optional[float] = None
    arrival_time: Optional[datetime] = None
    arrival_seal_qr: Optional[str] = None


class TransportRecordResponse(BaseModel):
    """运输记录详情响应"""
    id: int
    vehicle_id: int

    # 出港信息
    departure_port: Optional[str]
    departure_weight: Optional[float]
    departure_net_weight: Optional[float]
    departure_time: Optional[datetime]
    departure_seal_id: Optional[int]

    # 进厂信息
    arrival_weight: Optional[float]
    arrival_net_weight: Optional[float]
    arrival_time: Optional[datetime]
    arrival_seal_id: Optional[int]

    # 计算字段
    weight_diff: Optional[float]
    weight_diff_ratio: Optional[float]
    transport_duration: Optional[int]

    # 状态
    status: RecordStatus
    alert_count: int
    notes: Optional[str]

    created_at: datetime
    updated_at: datetime

    # 嵌套关联数据（可选）
    vehicle_plate: Optional[str] = None   # 车牌号（从vehicle关联获取）
    seals: Optional[List[SealRecordResponse]] = None

    model_config = ConfigDict(from_attributes=True)


class TransportListItem(BaseModel):
    """运输记录列表项（简化版）"""
    id: int
    vehicle_id: int
    vehicle_plate: Optional[str] = None
    departure_port: Optional[str]
    departure_time: Optional[datetime]
    arrival_time: Optional[datetime]
    departure_net_weight: Optional[float]
    arrival_net_weight: Optional[float]
    weight_diff_ratio: Optional[float]
    transport_duration: Optional[int]
    status: RecordStatus
    alert_count: int

    model_config = ConfigDict(from_attributes=True)


class TransportQueryParams(BaseModel):
    """运输记录查询参数"""
    page: int = 1
    size: int = 20
    plate_number: Optional[str] = None    # 按车牌筛选
    status: Optional[RecordStatus] = None  # 按状态筛选
    departure_port: Optional[str] = None   # 按港口筛选
    date_from: Optional[datetime] = None   # 开始时间
    date_to: Optional[datetime] = None     # 结束时间
