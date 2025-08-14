"""
系統用戶管理相關的 Pydantic 模型
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class CreateUserRequest(BaseModel):
    """創建用戶請求"""
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "admin"


class UpdateUserRequest(BaseModel):
    """更新用戶請求"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None  # 可選密碼更新
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """用戶響應"""
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    accessible_companies: List[dict] = []


class UserListResponse(BaseModel):
    """用戶列表響應"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


class UserStatsResponse(BaseModel):
    """用戶統計響應"""
    total_users: int
    active_users: int
    admin_users: int
    new_users_this_month: int