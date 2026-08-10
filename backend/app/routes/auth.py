"""
认证相关路由
"""
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_password_hash,
    get_current_user_dependency,
)
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    RefreshTokenRequest,
    LoginRequest,
    RegisterRequest,
    UserResponse,
    UserUpdateRequest,
    UserRoleUpdateRequest,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db = Depends(get_db)
):
    """
    用户登录
    """
    user = await authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=refresh_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db = Depends(get_db)
):
    """
    刷新访问令牌
    """
    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
        )
    
    username = payload.get("sub")
    user_id = payload.get("user_id")
    
    # 验证用户是否存在
    user = await db.get(User, user_id)
    if not user or user.username != username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # 返回原刷新令牌
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    db = Depends(get_db)
):
    """
    用户注册
    """
    # 检查用户名是否已存在
    existing_user = await db.execute(
        User.__table__.select().where(User.username == request.username)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    
    # 检查邮箱是否已存在
    existing_email = await db.execute(
        User.__table__.select().where(User.email == request.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在",
        )
    
    # 创建新用户
    hashed_password = get_password_hash(request.password)
    user = User(
        username=request.username,
        email=request.email,
        hashed_password=hashed_password,
        full_name=request.full_name,
        company=request.company,
        role="user"  # 默认用户角色
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.from_orm(user)


@router.get("/check-username")
async def check_username_availability(
    username: str,
    db = Depends(get_db)
):
    """
    检查用户名是否可用
    """
    existing_user = await db.execute(
        User.__table__.select().where(User.username == username)
    )
    available = existing_user.scalar_one_or_none() is None
    return {"available": available}


@router.get("/check-email")
async def check_email_availability(
    email: str,
    db = Depends(get_db)
):
    """
    检查邮箱是否可用
    """
    existing_email = await db.execute(
        User.__table__.select().where(User.email == email)
    )
    available = existing_email.scalar_one_or_none() is None
    return {"available": available}


@router.post("/logout")
async def logout():
    """
    用户登出
    注意：JWT是无状态的，客户端需要删除本地存储的令牌
    """
    return {"message": "登出成功"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    db = Depends(get_db)
):
    """
    获取当前登录用户信息
    """
    # 从请求头获取token
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌"
        )
    
    # 验证令牌格式
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌格式错误，应为 'Bearer <token>'"
        )
    
    token = parts[1]
    
    # 验证令牌并获取用户
    from app.core.security import verify_access_token
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的令牌"
        )
    
    username = payload.get("sub")
    user_id = payload.get("user_id")
    
    if not username or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌载荷"
        )
    
    # 查询用户
    from sqlalchemy import select
    stmt = select(User).where(User.id == user_id, User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse.from_orm(user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    update_data: UserUpdateRequest,
    request: Request,
    db = Depends(get_db)
):
    """
    更新当前登录用户信息
    """
    # 从请求头获取token
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌"
        )
    
    # 验证令牌格式
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌格式错误，应为 'Bearer <token>'"
        )
    
    token = parts[1]
    
    # 验证令牌并获取用户
    from app.core.security import verify_access_token
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的令牌"
        )
    
    username = payload.get("sub")
    user_id = payload.get("user_id")
    
    if not username or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌载荷"
        )
    
    # 查询用户
    from sqlalchemy import select
    stmt = select(User).where(User.id == user_id, User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新用户信息
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.from_orm(user)


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_data: UserRoleUpdateRequest,
    request: Request,
    db = Depends(get_db)
):
    """
    更新用户角色（仅管理员可用）
    """
    # 从请求头获取token
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌"
        )
    
    # 验证令牌格式
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌格式错误，应为 'Bearer <token>'"
        )
    
    token = parts[1]
    
    # 验证令牌并获取当前用户（管理员）
    from app.core.security import verify_access_token
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的令牌"
        )
    
    admin_username = payload.get("sub")
    admin_user_id = payload.get("user_id")
    
    if not admin_username or not admin_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌载荷"
        )
    
    # 查询管理员用户
    from sqlalchemy import select
    admin_stmt = select(User).where(User.id == admin_user_id, User.username == admin_username)
    admin_result = await db.execute(admin_stmt)
    admin_user = admin_result.scalar_one_or_none()
    
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )
    
    # 检查当前用户是否为管理员
    if admin_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改用户角色"
        )
    
    # 查询要修改的用户
    user_stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="要修改的用户不存在"
        )
    
    # 验证角色值
    valid_roles = ["user", "reviewer", "admin"]
    if role_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色值。有效角色：{', '.join(valid_roles)}"
        )
    
    # 更新用户角色
    user.role = role_data.role
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.from_orm(user)