"""
API 路由配置
"""
from fastapi import APIRouter

from app.routes import auth, contract, review, stats, user, admin, reviewer

# 创建主路由器
api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(contract.router, prefix="/contracts", tags=["合同管理"])
api_router.include_router(review.router, prefix="/contracts", tags=["合同审核"])
api_router.include_router(stats.router, prefix="/stats", tags=["统计"])
api_router.include_router(user.router, prefix="/user", tags=["用户功能"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理员功能"])
api_router.include_router(reviewer.router, prefix="/reviewer", tags=["审核员工作台"])