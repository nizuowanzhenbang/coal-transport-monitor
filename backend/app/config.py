"""应用配置管理"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./coal_transport.db"

    # JWT认证配置
    SECRET_KEY: str = "coal-transport-secret-key-please-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # 应用基本配置
    APP_NAME: str = "汽车运煤智能监督与风险预警系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 重量异常检测阈值
    WEIGHT_DIFF_THRESHOLD: float = 0.003  # 固定阈值 3‰
    WEIGHT_DYNAMIC_K_GENERAL: float = 2.0  # 动态阈值系数（一般预警）
    WEIGHT_DYNAMIC_K_SEVERE: float = 3.0   # 动态阈值系数（严重预警）

    # 时间异常检测阈值（分钟）
    TIME_GENERAL_OVERTIME_MINUTES: int = 30   # 一般超时阈值
    TIME_SEVERE_OVERTIME_MINUTES: int = 60    # 严重超时阈值
    TIME_DEFAULT_BASELINE_MINUTES: int = 240  # 默认基准运输时长

    # 历史数据分析窗口
    HISTORICAL_WINDOW_SIZE: int = 100  # 最近N条记录用于动态阈值计算
    MIN_HISTORICAL_SIZE: int = 10      # 动态阈值最少历史样本数

    model_config = {"env_file": ".env", "case_sensitive": True}


# 全局配置实例
settings = Settings()
