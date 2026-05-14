"""预警记录模型"""
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class AlertType(str, enum.Enum):
    """预警类型枚举"""
    WEIGHT_SHORTAGE = "WEIGHT_SHORTAGE"  # 重量亏损（进厂低于出港）
    WEIGHT_OVERAGE = "WEIGHT_OVERAGE"    # 重量盈余（进厂高于出港）
    TIME_EXCESSIVE = "TIME_EXCESSIVE"    # 运输超时
    SEAL_MISMATCH = "SEAL_MISMATCH"      # 铅封二维码不匹配
    SEAL_DAMAGED = "SEAL_DAMAGED"        # 铅封损坏或无法识别


class Severity(str, enum.Enum):
    """预警严重程度枚举"""
    GENERAL = "GENERAL"  # 一般预警
    SEVERE = "SEVERE"    # 严重预警


class AlertStatus(str, enum.Enum):
    """预警处理状态枚举"""
    PENDING = "PENDING"            # 待处理
    ACKNOWLEDGED = "ACKNOWLEDGED"  # 已确认
    RESOLVED = "RESOLVED"          # 已解决
    DISMISSED = "DISMISSED"        # 已忽略


class Alert(Base):
    """预警记录表：自动生成，记录每次运输的异常情况"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    # 外键：关联运输记录
    transport_id = Column(
        Integer, ForeignKey("transport_records.id"), nullable=False, index=True, comment="关联运输记录ID"
    )

    # 预警信息
    alert_type = Column(Enum(AlertType), nullable=False, comment="预警类型")
    severity = Column(Enum(Severity), nullable=False, comment="严重程度")
    description = Column(Text, nullable=False, comment="预警描述")
    threshold_value = Column(Float, nullable=True, comment="触发阈值")
    actual_value = Column(Float, nullable=True, comment="实际检测值")

    # 处理信息
    status = Column(
        Enum(AlertStatus),
        default=AlertStatus.PENDING,
        nullable=False,
        comment="处理状态",
    )
    resolved_by = Column(String(50), nullable=True, comment="处理人用户名")
    resolved_at = Column(DateTime, nullable=True, comment="处理时间")
    resolution_notes = Column(Text, nullable=True, comment="处理备注")

    created_at = Column(DateTime, default=datetime.utcnow, comment="预警生成时间")

    # 多对一：属于某条运输记录
    transport = relationship("TransportRecord", back_populates="alerts")
