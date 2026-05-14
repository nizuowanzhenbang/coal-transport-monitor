"""模型包：导入所有ORM模型，确保SQLAlchemy mapper完整注册"""
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.transport import TransportRecord, RecordStatus
from app.models.seal import SealRecord, SealType
from app.models.alert import Alert, AlertType, Severity, AlertStatus
from app.models.user import User, UserRole

__all__ = [
    "Vehicle",
    "VehicleStatus",
    "TransportRecord",
    "RecordStatus",
    "SealRecord",
    "SealType",
    "Alert",
    "AlertType",
    "Severity",
    "AlertStatus",
    "User",
    "UserRole",
]
