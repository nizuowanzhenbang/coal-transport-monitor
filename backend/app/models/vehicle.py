"""车辆信息模型"""
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Enum, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class VehicleStatus(str, enum.Enum):
    """车辆状态枚举"""
    ACTIVE = "ACTIVE"      # 正常运营
    INACTIVE = "INACTIVE"  # 已停用


class Vehicle(Base):
    """车辆信息表"""
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(20), unique=True, nullable=False, index=True, comment="车牌号")
    tare_weight = Column(Float, nullable=False, comment="皮重(kg)")
    driver_name = Column(String(50), nullable=False, comment="司机姓名")
    driver_phone = Column(String(20), nullable=True, comment="司机电话")
    status = Column(
        Enum(VehicleStatus),
        default=VehicleStatus.ACTIVE,
        nullable=False,
        comment="车辆状态",
    )
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 一辆车对应多条运输记录
    transports = relationship("TransportRecord", back_populates="vehicle")
