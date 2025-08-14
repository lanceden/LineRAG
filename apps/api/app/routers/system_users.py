"""
系統管理員 API 路由 - JWT 認證版本
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.auth import (
    authenticate_user, 
    get_current_user, 
    require_admin, 
    require_super_admin,
    AuthService
)
from app.models.system_user import SystemUser
from app.models.company import Company
from app.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    RefreshTokenRequest, 
    TokenResponse,
    UserInfo,
    CompanyInfo
)
from app.schemas.system_user import (
    CreateUserRequest,
    UpdateUserRequest, 
    UserResponse,
    UserListResponse,
    UserStatsResponse
)

router = APIRouter(prefix="/system-users", tags=["系統管理員"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """系統管理員登入 - JWT 版本"""
    # 驗證用戶
    user = authenticate_user(request.email, request.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤"
        )
    
    # 生成 JWT tokens
    token_data = {"user_id": user.id, "username": user.username, "role": user.role}
    access_token = AuthService.create_access_token(token_data)
    refresh_token = AuthService.create_refresh_token(token_data)
    
    # 更新登入時間
    user.last_login = datetime.utcnow()
    db.commit()
    
    # 準備用戶資訊
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at
    )
    
    # 準備可訪問的公司列表
    accessible_companies = [
        CompanyInfo(
            id=company.id,
            name=company.name,
            code=company.code,
            is_active=company.is_active
        )
        for company in user.accessible_companies
    ]
    
    return LoginResponse(
        success=True,
        message="登入成功",
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_info,
        accessible_companies=accessible_companies
    )


@router.get("/profile")
async def get_profile(request: Request):
    """獲取系統用戶資料"""
    from app.core.middleware import get_current_user_from_state
    current_user = get_current_user_from_state(request)
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "last_login": current_user.last_login,
        "created_at": current_user.created_at,
        "accessible_companies": [
            {
                "id": company.id,
                "name": company.name,
                "code": company.code,
                "is_active": company.is_active
            }
            for company in current_user.accessible_companies
        ]
    }


@router.get("/companies")
async def get_accessible_companies(
    request: Request,
    db: Session = Depends(get_db)
):
    """獲取可管理的公司列表"""
    from app.core.middleware import get_current_user_from_state
    current_user = get_current_user_from_state(request)
    if current_user.is_super_admin:
        # 超級管理員可以看所有公司
        companies = db.query(Company).filter(Company.is_active == True).all()
    else:
        companies = current_user.accessible_companies
    
    return [
        {
            "id": company.id,
            "name": company.name,
            "code": company.code,
            "subscription_plan": company.subscription_plan,
            "max_documents": company.max_documents,
            "is_active": company.is_active,
            "created_at": company.created_at
        }
        for company in companies
    ]


@router.post("/companies/{company_id}/access")
async def grant_company_access(
    company_id: int,
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """授予系統用戶公司管理權限"""
    from app.core.middleware import require_super_admin_permission
    current_user = require_super_admin_permission(request)
    
    user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not user or not company:
        raise HTTPException(status_code=404, detail="用戶或公司不存在")
    
    if company not in user.accessible_companies:
        user.accessible_companies.append(company)
        db.commit()
    
    return {"success": True, "message": "權限授予成功"}


@router.delete("/companies/{company_id}/access/{user_id}")
async def revoke_company_access(
    company_id: int,
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """撤銷系統用戶公司管理權限"""
    from app.core.middleware import require_super_admin_permission
    current_user = require_super_admin_permission(request)
    
    user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not user or not company:
        raise HTTPException(status_code=404, detail="用戶或公司不存在")
    
    if company in user.accessible_companies:
        user.accessible_companies.remove(company)
        db.commit()
    
    return {"success": True, "message": "權限撤銷成功"}


@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = 1,
    page_size: int = 20,
    role: str = None,
    search: str = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """獲取用戶列表"""
    from app.core.middleware import require_super_admin_permission
    current_user = require_super_admin_permission(request)
    
    query = db.query(SystemUser)
    
    # 角色篩選
    if role:
        query = query.filter(SystemUser.role == role)
    
    # 搜尋篩選
    if search:
        query = query.filter(
            SystemUser.username.contains(search) |
            SystemUser.email.contains(search) |
            SystemUser.full_name.contains(search)
        )
    
    # 計算總數
    total = query.count()
    
    # 分頁
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()
    
    # 轉換為響應格式
    user_responses = []
    for user in users:
        accessible_companies = [
            {"id": company.id, "name": company.name}
            for company in user.accessible_companies
        ]
        user_responses.append(UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
            accessible_companies=accessible_companies
        ))
    
    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: CreateUserRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """創建新用戶"""
    from app.core.middleware import require_super_admin_permission
    current_user = require_super_admin_permission(request)
    
    # 檢查用戶名和郵箱是否已存在
    existing_user = db.query(SystemUser).filter(
        (SystemUser.username == user_data.username) |
        (SystemUser.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="用戶名或郵箱已存在"
        )
    
    # 創建新用戶
    password_hash = AuthService.get_password_hash(user_data.password)
    new_user = SystemUser(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name,
        role=user_data.role,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        is_active=new_user.is_active,
        last_login=new_user.last_login,
        created_at=new_user.created_at,
        accessible_companies=[]
    )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """獲取用戶統計"""
    from app.core.middleware import require_super_admin_permission
    current_user = require_super_admin_permission(request)
    
    total_users = db.query(SystemUser).count()
    active_users = db.query(SystemUser).filter(SystemUser.is_active == True).count()
    admin_users = db.query(SystemUser).filter(SystemUser.role.in_(["super_admin", "admin"])).count()
    
    # 本月新增用戶
    from datetime import datetime, timedelta
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month = db.query(SystemUser).filter(
        SystemUser.created_at >= start_of_month
    ).count()
    
    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        new_users_this_month=new_users_this_month
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UpdateUserRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """更新用戶"""
    from app.core.middleware import require_super_admin_permission
    current_user = require_super_admin_permission(request)
    
    user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    # 更新用戶資料
    update_data = user_data.dict(exclude_unset=True)
    print(f"Update data received: {update_data}")  # Debug log
    
    # 如果有密碼更新，需要進行加密
    if 'password' in update_data:
        print(f"Password update detected: {update_data['password'][:3]}...")  # Debug log (only first 3 chars)
        from app.core.auth import AuthService
        update_data['password_hash'] = AuthService.get_password_hash(update_data['password'])
        del update_data['password']  # 移除原始密碼
        print("Password hashed and added to update_data")  # Debug log
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    accessible_companies = [
        {"id": company.id, "name": company.name}
        for company in user.accessible_companies
    ]
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        accessible_companies=accessible_companies
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """刪除用戶"""
    from app.core.middleware import require_super_admin_permission
    current_user = require_super_admin_permission(request)
    
    user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    # 不能刪除自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能刪除自己的帳號")
    
    db.delete(user)
    db.commit()
    
    return {"success": True, "message": "用戶已刪除"}