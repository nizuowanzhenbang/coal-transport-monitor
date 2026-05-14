"""车辆相关Pydantic schemas"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.vehicle import VehicleStatus


class VehicleBase(BaseModel):
    """车辆基础字段"""
    plate_number: str
    tare_weight: float
    driver_name: str
    driver_phone: Optional[str] = None


class VehicleCreate(VehicleBase):
    """创建车辆请求体"""

    @field_validator("tare_weight")
    @classmethod
    def validate_tare_weight(cls, v: float) -> float:
        # 皮重应在合理范围内（8吨到20吨）
        if not (8000 <= v <= 20000):
            raise ValueError("皮重应在8000kg到20000kg之间")
        return v


class VehicleUpdate(BaseModel):
    """更新车辆请求体（所有字段可选）"""
    tare_weight: Optional[float] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    status: Optional[VehicleStatus] = None


class VehicleResponse(VehicleBase):
    """车辆详情响应"""
    id: int
    status: VehicleStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleListItem(BaseModel):
    """车辆列表项（含统计信息）"""
    id: int
    plate_number: str
    tare_weight: float
    driver_name: str
    driver_phone: Optional[str]
    status: VehicleStatus
    transport_count: int = 0      # 运输次数
    alert_count: int = 0          # 累计预警次数
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
