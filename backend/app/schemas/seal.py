"""铅封相关Pydantic schemas"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.seal import SealType


class SealRecordCreate(BaseModel):
    """创建铅封记录请求体"""
    qr_code: Optional[str] = None
    seal_type: SealType
    is_valid: bool = True
    scan_time: Optional[datetime] = None
    image_url: Optional[str] = None
    transport_id: Optional[int] = None


class SealRecordResponse(BaseModel):
    """铅封记录响应"""
    id: int
    qr_code: Optional[str]
    seal_type: SealType
    is_valid: bool
    scan_time: Optional[datetime]
    image_url: Optional[str]
    transport_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)
