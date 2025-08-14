"""
認證相關的 Pydantic 模型
"""

from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class LoginRequest(BaseModel):
    """登入請求"""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Token 響應"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """刷新 Token 請求"""
    refresh_token: str


class UserInfo(BaseModel):
    """用戶資訊"""
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime


class CompanyInfo(BaseModel):
    """公司資訊"""
    id: int
    name: str
    code: str
    is_active: bool


class LoginResponse(BaseModel):
    """登入響應"""
    success: bool
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInfo
    accessible_companies: List[CompanyInfo]