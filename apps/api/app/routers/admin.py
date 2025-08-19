"""
系統管理 API 路由
權限檢查由 PermissionMiddleware 自動處理
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.middleware import get_current_user
from app.models.company import Company
from app.models.system_user import SystemUser
from app.services.multitenant_user import get_multitenant_user_service

router = APIRouter(prefix="/admin", tags=["系統管理"])


@router.get("/companies")
async def list_all_companies(
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """獲取所有公司列表 - 需要 company.view 權限"""
    companies = db.query(Company).all()
    return [
        {
            "id": company.id,
            "name": company.name,
            "code": company.code,
            "is_active": company.is_active,
            "created_at": company.created_at,
        }
        for company in companies
    ]


@router.get("/users")
async def list_all_users(
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """獲取所有系統用戶列表 - 需要 user.view 權限"""
    users = db.query(SystemUser).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
        for user in users
    ]


@router.get("/system-info")
async def get_system_info(
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """獲取系統資訊 - 需要 system.analytics.view 權限"""
    total_companies = db.query(Company).count()
    active_companies = db.query(Company).filter(Company.is_active == True).count()
    total_users = db.query(SystemUser).count()
    active_users = db.query(SystemUser).filter(SystemUser.is_active == True).count()

    return {
        "companies": {
            "total": total_companies,
            "active": active_companies,
        },
        "users": {
            "total": total_users,
            "active": active_users,
        },
    }
