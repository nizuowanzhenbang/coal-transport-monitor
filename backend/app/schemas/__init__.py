"""Schemas包：导出所有Pydantic数据验证模型"""
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleListItem
from app.schemas.seal import SealRecordCreate, SealRecordResponse
from app.schemas.transport import (
    TransportRecordCreate,
    TransportRecordUpdate,
    TransportRecordResponse,
    TransportListItem,
)
from app.schemas.alert import (
    AlertResponse,
    AlertAcknowledgeRequest,
    AlertResolveRequest,
    AlertStats,
)
from app.schemas.dashboard import (
    OverviewData,
    AlertTrendItem,
    TopRiskVehicle,
    WeightDistributionItem,
)
from app.schemas.user import UserCreate, UserResponse, Token, LoginRequest

__all__ = [
    "VehicleCreate",
    "VehicleUpdate",
    "VehicleResponse",
    "VehicleListItem",
    "SealRecordCreate",
    "SealRecordResponse",
    "TransportRecordCreate",
    "TransportRecordUpdate",
    "TransportRecordResponse",
    "TransportListItem",
    "AlertResponse",
    "AlertAcknowledgeRequest",
    "AlertResolveRequest",
    "AlertStats",
    "OverviewData",
    "AlertTrendItem",
    "TopRiskVehicle",
    "WeightDistributionItem",
    "UserCreate",
    "UserResponse",
    "Token",
    "LoginRequest",
]
