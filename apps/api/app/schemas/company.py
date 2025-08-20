"""
公司管理相關的 Pydantic 模型
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl


class CompanyBase(BaseModel):
    """公司基本資訊"""
    name: str
    code: str
    description: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None


class CompanyCreate(CompanyBase):
    """建立公司請求"""
    # LINE 設定 (可選)
    line_channel_token: Optional[str] = None
    line_channel_secret: Optional[str] = None
    line_bot_enabled: bool = True
    
    # 訂閱設定
    subscription_plan: str = "standard"
    max_documents: int = 1000
    max_queries_per_month: int = 10000
    storage_quota_gb: int = 10


class CompanyUpdate(BaseModel):
    """更新公司請求"""
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    
    # LINE 設定
    line_channel_token: Optional[str] = None
    line_channel_secret: Optional[str] = None
    line_bot_enabled: Optional[bool] = None
    
    # 訂閱設定
    subscription_plan: Optional[str] = None
    max_documents: Optional[int] = None
    max_queries_per_month: Optional[int] = None
    storage_quota_gb: Optional[int] = None
    
    # 狀態
    is_active: Optional[bool] = None


class CompanyStats(BaseModel):
    """公司統計資訊"""
    total_users: int = 0
    active_users: int = 0
    total_documents: int = 0
    total_conversations: int = 0
    monthly_conversations: int = 0
    storage_used: int = 0  # bytes
    storage_limit: int = 0  # bytes
    last_activity: Optional[datetime] = None


class Company(CompanyBase):
    """公司完整資訊"""
    id: int
    
    # LINE 設定
    line_channel_token: Optional[str] = None
    line_channel_secret: Optional[str] = None
    line_bot_enabled: bool = True
    
    # 訂閱設定
    subscription_plan: str = "standard"
    max_documents: int = 1000
    max_queries_per_month: int = 10000
    storage_quota_gb: int = 10
    
    # 系統設定
    
    # 狀態和時間
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 統計資訊 (可選)
    stats: Optional[CompanyStats] = None

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    """公司列表回應"""
    companies: List[Company]
    total: int
    page: int = 1
    limit: int = 20
    has_next: bool = False
    has_prev: bool = False


class CompanyUserBase(BaseModel):
    """公司用戶基本資訊"""
    email: EmailStr
    name: str
    role: str  # company_admin, cs_manager, cs_agent


class CompanyUserCreate(CompanyUserBase):
    """邀請公司用戶請求"""
    permissions: Optional[List[str]] = None


class CompanyUser(CompanyUserBase):
    """公司用戶完整資訊"""
    id: int
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    permissions: Optional[List[str]] = None

    class Config:
        from_attributes = True


class CompanyUserListResponse(BaseModel):
    """公司用戶列表回應"""
    users: List[CompanyUser]
    total: int
    page: int = 1
    limit: int = 20


class CompanyInvitation(BaseModel):
    """公司邀請"""
    id: str
    company_id: int
    email: EmailStr
    name: str
    role: str
    invited_by: int
    invited_at: datetime
    expires_at: datetime
    is_accepted: bool = False
    accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyActivity(BaseModel):
    """公司活動記錄"""
    id: str
    company_id: int
    user_id: Optional[int] = None
    action: str  # created, updated, activated, deactivated, user_invited, user_joined, settings_changed
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BatchOperationRequest(BaseModel):
    """批次操作請求"""
    operation: str  # activate, deactivate, delete
    company_ids: List[int]


class BatchOperationResponse(BaseModel):
    """批次操作回應"""
    success: int
    failed: int
    errors: Optional[List[dict]] = None


class CompanySearchRequest(BaseModel):
    """公司搜尋請求"""
    query: str
    limit: int = 10
    filters: Optional[dict] = None


class CompanySearchResult(BaseModel):
    """公司搜尋結果"""
    company: Company
    relevance_score: float
    matched_fields: List[str]
    highlights: Optional[dict] = None


class CompanySearchResponse(BaseModel):
    """公司搜尋回應"""
    results: List[CompanySearchResult]
    total: int
    query: str
    took: int  # 搜尋耗時 (ms)


class CompanyExportOptions(BaseModel):
    """公司匯出選項"""
    format: str = "csv"  # csv, xlsx, json
    include_users: bool = True
    include_stats: bool = True
    include_settings: bool = False
    date_range: Optional[dict] = None


class CompanyImportOptions(BaseModel):
    """公司匯入選項"""
    format: str = "csv"  # csv, xlsx, json
    update_existing: bool = False
    skip_duplicates: bool = True
    default_settings: Optional[dict] = None


# API 回應模型
class ApiResponse(BaseModel):
    """標準 API 回應"""
    success: bool
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """錯誤回應"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None
