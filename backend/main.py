"""
FastAPI 主应用入口
中小企业智能合同审查平台
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import time
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.routes import api_router
# from app.middleware.auth_middleware import AuthMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 应用生命周期事件处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器"""
    # 启动逻辑
    logger.info("启动中小企业智能合同审查平台...")
    try:
        # 创建数据库表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        # 继续启动，但记录错误
    
    yield
    
    # 关闭逻辑
    logger.info("关闭中小企业智能合同审查平台...")

# 创建 FastAPI 应用
app = FastAPI(
    title="中小企业智能合同审查平台",
    description="基于 FastAPI 的 AI 合同审核系统",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加认证中间件（暂时注释）
# app.add_middleware(AuthMiddleware)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else "Internal Server Error"
        }
    )

# 请求计时中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 挂载静态文件 - 暂时注释掉，因为static目录可能不存在
# app.mount("/static", StaticFiles(directory="static"), name="static")

# 包含 API 路由
app.include_router(api_router, prefix="/api/v1")

# 健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "contract-review-platform",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )