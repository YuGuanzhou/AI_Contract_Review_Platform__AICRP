"""
管理员相关路由
提供管理员管理用户、系统配置等功能
"""
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.sql import text

from app.core.database import get_db
from app.core.security import get_current_user_dependency
from app.models.user import User
from app.schemas.auth import (
    UserResponse,
    UserRoleUpdateRequest,
    UserUpdateRequest,
    AdminUserUpdateRequest,
)

class PaginatedUserResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int

    class Config:
        from_attributes = True

router = APIRouter()


@router.get("/users", response_model=PaginatedUserResponse)
async def get_user_list(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="每页数量（兼容别名）"),
    search: Optional[str] = Query(None, description="搜索用户名或邮箱"),
    role: Optional[str] = Query(None, description="角色筛选: user, reviewer, admin"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    is_verified: Optional[bool] = Query(None, description="是否已验证"),
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户列表（仅管理员可用）
    """
    # 检查权限
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    # 使用 page_size 如果提供，否则使用 per_page
    actual_per_page = page_size if page_size is not None else per_page

    # 构建查询
    query = select(User).order_by(User.id.desc())

    # 应用筛选条件
    filters = []
    if search:
        filters.append(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )
    if role:
        filters.append(User.role == role)
    if is_active is not None:
        filters.append(User.is_active == is_active)
    if is_verified is not None:
        filters.append(User.is_verified == is_verified)

    if filters:
        query = query.where(and_(*filters))

    # 分页
    offset = (page - 1) * actual_per_page
    query = query.offset(offset).limit(actual_per_page)

    # 执行查询
    result = await db.execute(query)
    users = result.scalars().all()

    # 查询总数
    count_query = select(func.count()).select_from(User)
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 返回分页用户列表
    return PaginatedUserResponse(
        items=users,
        total=total,
        page=page,
        page_size=actual_per_page
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_detail(
    user_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户详情（仅管理员可用）
    """
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    update_data: AdminUserUpdateRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    更新用户信息（仅管理员可用）
    可以更新用户的基本信息、角色、激活状态等
    """
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    # 查询用户
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 验证角色值（如果提供了角色）
    if update_data.role is not None:
        valid_roles = ["user", "reviewer", "admin"]
        if update_data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的角色值。有效角色：{', '.join(valid_roles)}"
            )

    # 更新字段
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user


@router.patch("/users/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    切换用户激活状态（仅管理员可用）
    """
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 切换激活状态
    user.is_active = not user.is_active

    await db.commit()
    await db.refresh(user)

    return user


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role_admin(
    user_id: int,
    role_data: UserRoleUpdateRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    更新用户角色（仅管理员可用）
    此端点与auth.py中的功能重复，但使用统一的权限检查
    """
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    # 查询用户
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 验证角色值
    valid_roles = ["user", "reviewer", "admin"]
    if role_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色值。有效角色：{', '.join(valid_roles)}"
        )

    # 更新角色
    user.role = role_data.role

    await db.commit()
    await db.refresh(user)

    return user