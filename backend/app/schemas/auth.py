"""
认证相关的 Pydantic 模式
"""
from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str
    user: "UserResponse"
    
    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    company: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    full_name: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)


class UserRoleUpdateRequest(BaseModel):
    """用户角色更新请求（仅管理员可用）"""
    role: str = Field(..., description="用户角色：user（普通用户）、reviewer（审核员）、admin（管理员）")


class PasswordChangeRequest(BaseModel):
    """密码修改请求"""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)


class AdminUserUpdateRequest(BaseModel):
    """管理员用户更新请求"""
    full_name: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field(None, description="用户角色：user（普通用户）、reviewer（审核员）、admin（管理员）")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_verified: Optional[bool] = Field(None, description="是否已验证")


# 更新前向引用
TokenResponse.update_forward_refs()