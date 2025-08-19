"""
權限管理 API 路由
權限檢查由 PermissionMiddleware 自動處理
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_user
from app.models.system_user import SystemUser
from app.models.permission import UserPermission
from app.services.permission_service import PermissionService
from app.schemas.permission import (
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    UserPermissionSet,
    UserPermissionResponse,
)

router = APIRouter(prefix="/permissions", tags=["權限管理"])


@router.get("/matrix")
async def get_permission_matrix(
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """獲取權限矩陣資料 - 需要 user.permission 權限"""
    from app.models.system_user import SystemUser as SystemUserModel
    from app.models.company import Company

    # 獲取所有用戶
    users = db.query(SystemUserModel).filter(SystemUserModel.is_active == True).all()

    # 獲取所有權限
    permissions = PermissionService.get_all_permissions(db, is_active=True)

    # 獲取所有公司
    companies = db.query(Company).filter(Company.is_active == True).all()

    # 獲取所有用戶權限
    user_permissions_list = db.query(UserPermission).all()
    user_permissions_dict = {up.user_id: up for up in user_permissions_list}

    # 組織權限矩陣資料
    permission_matrix = {}
    company_matrix = {}

    for user in users:
        user_perm = user_permissions_dict.get(user.id)
        permission_matrix[user.id] = user_perm.granted_permissions if user_perm else []
        company_matrix[user.id] = user_perm.accessible_companies if user_perm else []

    return {
        "users": [
            {"id": u.id, "username": u.username, "full_name": u.full_name}
            for u in users
        ],
        "permissions": [
            {"code": p.code, "name": p.name, "category": p.category}
            for p in permissions
        ],
        "companies": [{"id": str(c.id), "name": c.name} for c in companies],
        "permission_matrix": permission_matrix,
        "company_matrix": company_matrix,
    }


@router.post("/matrix/toggle")
async def toggle_permission_matrix(
    user_id: int,
    permission_code: str,
    granted: bool,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """切換用戶權限 - 需要 user.permission 權限"""
    if granted:
        PermissionService.add_user_permission(db, user_id, permission_code)
    else:
        PermissionService.remove_user_permission(db, user_id, permission_code)

    return {"success": True}


@router.post("/matrix/company-access")
async def toggle_company_access_matrix(
    user_id: int,
    company_id: str,
    granted: bool,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """切換公司存取權限 - 需要 user.permission 權限"""
    if granted:
        PermissionService.add_user_company_access(db, user_id, company_id)
    else:
        PermissionService.remove_user_company_access(db, user_id, company_id)

    return {"success": True}
