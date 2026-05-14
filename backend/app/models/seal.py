"""铅封记录模型"""
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class SealType(str, enum.Enum):
    """铅封类型枚举"""
    DEPARTURE = "DEPARTURE"  # 出港铅封
    ARRIVAL = "ARRIVAL"      # 进厂铅封


class SealRecord(Base):
    """铅封记录表：记录出港和进厂两次铅封扫描信息"""
    __tablename__ = "seal_records"

    id = Column(Integer, primary_key=True, index=True)
    qr_code = Column(String(500), nullable=True, comment="铅封二维码内容")
    seal_type = Column(Enum(SealType), nullable=False, comment="铅封类型（出港/进厂）")
    is_valid = Column(Boolean, default=True, nullable=False, comment="二维码是否有效可识别")
    scan_time = Column(DateTime, nullable=True, comment="扫描时间")
    image_url = Column(String(500), nullable=True, comment="铅封照片URL")

    # 外键：关联运输记录
    transport_id = Column(
        Integer, ForeignKey("transport_records.id"), nullable=True, comment="关联运输记录ID"
    )

    # 多对一：铅封属于某条运输记录
    transport = relationship(
        "TransportRecord",
        back_populates="seals",
        foreign_keys=[transport_id],
    )
