"""用户模型"""
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime

from app.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "ADMIN"        # 管理员：全部权限
    OPERATOR = "OPERATOR"  # 操作员：增删改运输记录，处理预警
    VIEWER = "VIEWER"      # 查看者：只读


class User(Base):
    """用户表：系统用户和权限管理"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    hashed_password = Column(String(200), nullable=False, comment="加密后的密码")
    role = Column(
        Enum(UserRole),
        default=UserRole.VIEWER,
        nullable=False,
        comment="用户角色",
    )
    is_active = Column(Boolean, default=True, nullable=False, comment="账号是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
