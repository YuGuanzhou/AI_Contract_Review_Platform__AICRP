"""
安全相关功能模块
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.core.database import get_db

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        import bcrypt
        # 直接使用bcrypt验证，避免passlib的兼容性问题
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        # bcrypt.checkpw会自动处理密码长度限制
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"密码验证错误: {e}")
        return False


def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    import bcrypt
    # 直接使用bcrypt生成哈希，避免passlib的兼容性问题
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


async def authenticate_user(
    db,  # 移除AsyncSession类型注解
    username: str,
    password: str
) -> Optional[User]:
    """验证用户身份"""
    # 查询用户
    from sqlalchemy import select
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """验证令牌"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 检查令牌类型
        if payload.get("type") != token_type:
            return None
        
        # 检查过期时间
        expire = payload.get("exp")
        if expire is None or datetime.utcnow() > datetime.fromtimestamp(expire):
            return None
        
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """验证访问令牌"""
    return verify_token(token, "access")


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """验证刷新令牌"""
    return verify_token(token, "refresh")


def create_password_reset_token(email: str, user_id: int) -> str:
    """创建密码重置令牌（有效期由 PASSWORD_RESET_TOKEN_EXPIRE_MINUTES 控制）"""
    expire = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": email,
        "user_id": user_id,
        "type": "reset",
        "exp": expire,
    }
    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: str,
    db  # 移除AsyncSession类型注解
) -> Optional[User]:
    """获取当前用户"""
    from app.models.user import User as UserModel
    
    payload = verify_access_token(token)
    if not payload:
        return None
    
    username = payload.get("sub")
    user_id = payload.get("user_id")
    
    if username is None or user_id is None:
        return None
    
    # 查询用户
    from sqlalchemy import select
    stmt = select(UserModel).where(UserModel.id == user_id, UserModel.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    return user


async def get_current_active_user(
    token: str,
    db  # 移除AsyncSession类型注解
) -> User:
    """获取当前活跃用户"""
    from app.models.user import User as UserModel
    
    user = await get_current_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用",
        )
    
    return user


async def get_current_admin_user(
    token: str,
    db  # 移除AsyncSession类型注解
) -> User:
    """获取当前管理员用户"""
    from app.models.user import User as UserModel
    
    user = await get_current_active_user(token, db)
    
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足",
        )
    
    return user


async def get_current_user_dependency(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前用户的依赖函数
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
    
    # 使用现有的get_current_user函数
    user = await get_current_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    
    return user