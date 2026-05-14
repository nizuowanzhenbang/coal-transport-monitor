"""运输记录模型"""
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class RecordStatus(str, enum.Enum):
    """运输记录状态枚举"""
    NORMAL = "NORMAL"  # 正常
    ALERT = "ALERT"    # 一般预警
    SEVERE = "SEVERE"  # 严重预警


class TransportRecord(Base):
    """运输记录表（核心业务表）：记录煤炭从港口到电厂的完整运输过程"""
    __tablename__ = "transport_records"

    id = Column(Integer, primary_key=True, index=True)

    # 外键：关联车辆
    vehicle_id = Column(
        Integer, ForeignKey("vehicles.id"), nullable=False, index=True, comment="车辆ID"
    )

    # ---- 出港信息 ----
    departure_port = Column(String(100), nullable=True, comment="出发港口名称")
    departure_weight = Column(Float, nullable=True, comment="出港过磅毛重(kg)")
    departure_net_weight = Column(Float, nullable=True, comment="出港净重(kg) = 毛重 - 皮重")
    departure_time = Column(DateTime, nullable=True, comment="出港时间")
    # 应用层外键，指向铅封记录，不在DB层强制约束（避免SQLite循环FK问题）
    departure_seal_id = Column(Integer, nullable=True, comment="出港铅封ID（应用层外键）")

    # ---- 进厂信息 ----
    arrival_weight = Column(Float, nullable=True, comment="进厂过磅毛重(kg)")
    arrival_net_weight = Column(Float, nullable=True, comment="进厂净重(kg) = 毛重 - 皮重")
    arrival_time = Column(DateTime, nullable=True, comment="到达时间")
    # 应用层外键，指向铅封记录
    arrival_seal_id = Column(Integer, nullable=True, comment="进厂铅封ID（应用层外键）")

    # ---- 计算字段（创建时自动填充）----
    weight_diff = Column(Float, nullable=True, comment="重量差 = 进厂净重 - 出港净重")
    weight_diff_ratio = Column(Float, nullable=True, comment="重量偏差率 = 重量差 / 出港净重")
    transport_duration = Column(Integer, nullable=True, comment="运输耗时（分钟）")

    # ---- 状态字段 ----
    status = Column(
        Enum(RecordStatus),
        default=RecordStatus.NORMAL,
        nullable=False,
        comment="记录状态（正常/一般预警/严重预警）",
    )
    alert_count = Column(Integer, default=0, nullable=False, comment="累计预警次数")
    notes = Column(Text, nullable=True, comment="备注信息")

    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 多对一：属于一辆车
    vehicle = relationship("Vehicle", back_populates="transports")

    # 一对多：拥有多个铅封记录（出港+进厂各一个）
    seals = relationship(
        "SealRecord",
        back_populates="transport",
        foreign_keys="[SealRecord.transport_id]",
    )

    # 一对多：拥有多个预警记录
    alerts = relationship("Alert", back_populates="transport")
