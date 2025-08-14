"""
Admin API routes - 多租戶管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.company import Company
from app.models.system_user import SystemUser
from app.services.multitenant_user import get_multitenant_user_service

router = APIRouter(prefix="/admin", tags=["管理"])


@router.get("/companies")
async def list_all_companies(request: Request, db: Session = Depends(get_db)):
    """獲取所有公司列表（管理員功能）"""
    from app.core.middleware import require_admin_permission
    current_user = require_admin_permission(request)
    companies = db.query(Company).all()
    return [
        {
            "id": company.id,
            "name": company.name,
            "code": company.code,
            "subscription_plan": company.subscription_plan,
            "is_active": company.is_active,
            "created_at": company.created_at
        }
        for company in companies
    ]


@router.get("/system-stats")
async def get_system_stats(request: Request, db: Session = Depends(get_db)):
    """獲取系統統計資訊"""
    from app.core.middleware import require_admin_permission
    current_user = require_admin_permission(request)
    total_companies = db.query(Company).count()
    active_companies = db.query(Company).filter(Company.is_active == True).count()
    total_admins = db.query(SystemUser).count()
    
    return {
        "total_companies": total_companies,
        "active_companies": active_companies,
        "total_system_users": total_admins,
        "framework": "RAG-Anything + PostgreSQL Multi-Tenant",
        "version": "2.0.0"
    }
