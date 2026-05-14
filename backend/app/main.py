"""汽车运煤智能监督与风险预警系统 - FastAPI主入口"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import *  # 确保所有模型注册
from app.models.user import User, UserRole
from app.api import vehicles, transports, alerts, dashboard, auth
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_db():
    """初始化数据库表结构"""
    Base.metadata.create_all(bind=engine)


def create_default_admin():
    """创建默认管理员账户（如果不存在）"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                hashed_password=pwd_context.hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print("[初始化] 创建默认管理员: admin / admin123")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print(f"[启动] {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    create_default_admin()
    print("[启动] 数据库初始化完成")
    yield
    # 关闭时清理
    print("[关闭] 应用停止")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于港口—入厂数据比对的汽车运煤智能监督与风险预警系统",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """统一异常响应格式"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器内部错误: {str(exc)}",
            "data": None,
        },
    )


# 注册API路由
app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(transports.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)


@app.get("/", tags=["健康检查"])
def root():
    """系统健康检查"""
    return {
        "code": 200,
        "message": "汽车运煤智能监督与风险预警系统运行正常",
        "data": {
            "version": settings.APP_VERSION,
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["健康检查"])
def health_check():
    """健康检查端点"""
    return {"status": "ok"}
