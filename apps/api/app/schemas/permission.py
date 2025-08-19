"""
權限相關的 Pydantic schemas
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    """權限基礎模型"""

    code: str = Field(..., description="權限代碼")
    name: str = Field(..., description="權限名稱")
    description: Optional[str] = Field(None, description="權限描述")
    category: str = Field(default="功能權限", description="權限分類")


class PermissionCreate(PermissionBase):
    """創建權限請求"""

    pass


class PermissionUpdate(BaseModel):
    """更新權限請求"""

    name: Optional[str] = Field(None, description="權限名稱")
    description: Optional[str] = Field(None, description="權限描述")
    category: Optional[str] = Field(None, description="權限分類")
    is_active: Optional[bool] = Field(None, description="是否啟用")


class PermissionResponse(PermissionBase):
    """權限響應模型"""

    id: int = Field(..., description="權限 ID")
    is_active: bool = Field(..., description="是否啟用")
    created_at: datetime = Field(..., description="創建時間")
    updated_at: Optional[datetime] = Field(None, description="更新時間")

    class Config:
        from_attributes = True


class UserPermissionSet(BaseModel):
    """設置用戶權限請求"""

    permission_codes: List[str] = Field(
        default_factory=list, description="權限代碼列表"
    )
    company_ids: List[int] = Field(
        default_factory=list, description="可存取公司 ID 列表"
    )


class UserPermissionResponse(BaseModel):
    """用戶權限響應模型"""

    user_id: int = Field(..., description="用戶 ID")
    granted_permissions: List[str] = Field(
        default_factory=list, description="已授予的權限代碼"
    )
    accessible_companies: List[int] = Field(
        default_factory=list, description="可存取的公司 ID"
    )

    class Config:
        from_attributes = True


class PermissionMatrix(BaseModel):
    """權限矩陣模型（用於前端權限管理界面）"""

    user_id: int = Field(..., description="用戶 ID")
    user_name: str = Field(..., description="用戶名稱")
    permissions: dict = Field(
        ..., description="權限狀態字典，key 為權限代碼，value 為是否擁有該權限"
    )
    companies: dict = Field(
        ..., description="公司存取狀態字典，key 為公司 ID，value 為是否可存取"
    )


class PermissionCategory(BaseModel):
    """權限分類模型"""

    category: str = Field(..., description="分類名稱")
    permissions: List[PermissionResponse] = Field(..., description="該分類下的權限列表")


class PermissionSummary(BaseModel):
    """權限摘要統計"""

    total_permissions: int = Field(..., description="總權限數")
    active_permissions: int = Field(..., description="啟用權限數")
    categories: List[str] = Field(..., description="權限分類列表")
    users_with_permissions: int = Field(..., description="有權限的用戶數")
