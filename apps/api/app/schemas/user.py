"""
用戶管理相關的 Pydantic 模型
"""
from typing import Optional
from pydantic import BaseModel

class UserCreateRequest(BaseModel):
    """建立用戶請求"""
    line_id: str
    name: str
    email: Optional[str] = ""
    role: str = "cs"  # admin | cs

class UserRoleUpdateRequest(BaseModel):
    """更新用戶角色請求"""
    role: str  # admin | cs

class UserResponse(BaseModel):
    """用戶資訊響應"""
    line_id: str
    name: str
    email: str
    role: str
    is_active: bool
    created_at: int
    updated_at: int

class UserRoleResponse(BaseModel):
    """用戶角色響應（供NextAuth使用）"""
    line_id: str
    role: str
    is_active: bool
    name: str

class PermissionCheckResponse(BaseModel):
    """權限檢查響應"""
    line_id: str
    required_role: str
    has_permission: bool

class ApiResponse(BaseModel):
    """通用API響應"""
    success: bool
    message: str
    user: Optional[UserResponse] = None