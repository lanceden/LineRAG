"""
租戶用戶管理 API 路由（LINE Bot用戶）
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.services.multitenant_user import get_multitenant_user_service
from app.models.tenant_user import TenantUser
from app.models.company import Company

router = APIRouter(prefix="/tenant-users", tags=["租戶用戶管理"])


@router.post("/create")
async def create_tenant_user(
    company_id: int,
    line_id: str,
    name: str,
    role: str = "user",
    email: Optional[str] = None,
    line_display_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """建立新租戶用戶"""
    user_service = get_multitenant_user_service(db)

    try:
        user = await user_service.create_user(
            company_id=company_id,
            line_id=line_id,
            name=name,
            role=role,
            email=email,
            line_display_name=line_display_name,
        )

        return {
            "success": True,
            "message": "租戶用戶建立成功",
            "user": {
                "id": user.id,
                "company_id": user.company_id,
                "line_id": user.line_id,
                "name": user.name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立用戶失敗: {str(e)}")


@router.get("/line/{line_id}")
async def get_user_by_line_id(
    line_id: str, company_id: Optional[int] = None, db: Session = Depends(get_db)
):
    """根據LINE ID取得租戶用戶"""
    user_service = get_multitenant_user_service(db)
    user = await user_service.get_user_by_line_id(line_id, company_id)

    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    return {
        "id": user.id,
        "company_id": user.company_id,
        "line_id": user.line_id,
        "line_display_name": user.line_display_name,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "total_queries": user.total_queries,
        "monthly_queries": user.monthly_queries,
        "last_login": user.last_login,
        "created_at": user.created_at,
    }


@router.get("/line/{line_id}/company")
async def get_user_with_company(line_id: str, db: Session = Depends(get_db)):
    """取得用戶及其所屬公司資訊"""
    user_service = get_multitenant_user_service(db)
    result = await user_service.get_user_company(line_id)

    if not result:
        raise HTTPException(status_code=404, detail="用戶或公司不存在")

    user, company = result
    return {
        "user": {
            "id": user.id,
            "line_id": user.line_id,
            "name": user.name,
            "role": user.role,
            "is_active": user.is_active,
        },
        "company": {
            "id": company.id,
            "name": company.name,
            "code": company.code,
            "subscription_plan": company.subscription_plan,
            "is_active": company.is_active,
        },
    }


@router.get("/company/{company_id}")
async def list_company_users(company_id: int, db: Session = Depends(get_db)):
    """列出公司的所有租戶用戶"""
    user_service = get_multitenant_user_service(db)
    users = await user_service.get_company_users(company_id)

    return [
        {
            "id": user.id,
            "line_id": user.line_id,
            "line_display_name": user.line_display_name,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "total_queries": user.total_queries,
            "monthly_queries": user.monthly_queries,
            "last_login": user.last_login,
            "created_at": user.created_at,
        }
        for user in users
    ]


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: str,
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """更新租戶用戶角色"""
    if new_role not in ["admin", "cs", "user"]:
        raise HTTPException(status_code=400, detail="無效的角色")

    user = db.query(TenantUser).filter(TenantUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    if company_id and user.company_id != company_id:
        raise HTTPException(status_code=403, detail="無權限訪問此用戶")

    try:
        user.role = new_role
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "message": "角色更新成功",
            "user": {
                "id": user.id,
                "line_id": user.line_id,
                "name": user.name,
                "role": user.role,
                "company_id": user.company_id,
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失敗: {str(e)}")


@router.put("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int, company_id: Optional[int] = None, db: Session = Depends(get_db)
):
    """停用租戶用戶"""
    user = db.query(TenantUser).filter(TenantUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    if company_id and user.company_id != company_id:
        raise HTTPException(status_code=403, detail="無權限訪問此用戶")

    try:
        user.is_active = False
        db.commit()
        return {"success": True, "message": "用戶已停用"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"停用失敗: {str(e)}")


@router.post("/{user_id}/login")
async def update_login_time(user_id: int, db: Session = Depends(get_db)):
    """更新用戶登入時間"""
    user_service = get_multitenant_user_service(db)
    await user_service.update_user_login(user_id)
    return {"success": True, "message": "登入時間已更新"}


@router.post("/{user_id}/query")
async def increment_query_count(user_id: int, db: Session = Depends(get_db)):
    """增加用戶查詢次數"""
    user_service = get_multitenant_user_service(db)
    await user_service.increment_user_queries(user_id)
    return {"success": True, "message": "查詢次數已更新"}


@router.get("/{user_id}/permission/{required_role}")
async def check_user_permission(
    user_id: int, required_role: str, db: Session = Depends(get_db)
):
    """檢查用戶權限"""
    user_service = get_multitenant_user_service(db)
    has_permission = await user_service.check_user_permission(user_id, required_role)

    return {
        "user_id": user_id,
        "required_role": required_role,
        "has_permission": has_permission,
    }
