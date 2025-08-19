"""
系統用戶管理 API 路由
權限檢查由 PermissionMiddleware 自動處理
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.middleware import get_current_user
from app.core.auth import AuthService
from app.models.system_user import SystemUser
from app.schemas.system_user import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    UserListResponse,
    UserStatsResponse,
)

router = APIRouter(prefix="/system-users", tags=["系統用戶管理"])


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """獲取用戶統計 - 需要 user.view 權限"""
    from datetime import datetime, timedelta
    from sqlalchemy import func

    # 總用戶數
    total_users = db.query(SystemUser).count()

    # 啟用用戶數
    active_users = db.query(SystemUser).filter(SystemUser.is_active == True).count()

    # 停用用戶數
    inactive_users = total_users - active_users

    # 本月新增用戶數
    current_month_start = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    users_this_month = (
        db.query(SystemUser)
        .filter(SystemUser.created_at >= current_month_start)
        .count()
    )

    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        users_this_month=users_this_month,
    )


@router.get("/", response_model=UserListResponse)
async def get_system_users(
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(20, ge=1, le=100, description="每頁數量"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    is_active: Optional[bool] = Query(None, description="是否啟用"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """獲取系統用戶列表 - 需要 user.view 權限"""
    offset = (page - 1) * limit

    query = db.query(SystemUser)

    if search:
        query = query.filter(
            SystemUser.username.contains(search)
            | SystemUser.email.contains(search)
            | SystemUser.full_name.contains(search)
        )

    if is_active is not None:
        query = query.filter(SystemUser.is_active == is_active)

    total = query.count()
    users = query.offset(offset).limit(limit).all()

    return UserListResponse(
        users=[
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                last_login=user.last_login,
            )
            for user in users
        ],
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_system_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """獲取單一系統用戶 - 需要 user.view 權限"""
    user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        last_login=user.last_login,
    )


@router.post("/", response_model=UserResponse)
async def create_system_user(
    user_data: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """創建系統用戶 - 需要 user.create 權限"""
    # 檢查用戶名是否已存在
    existing_user = (
        db.query(SystemUser)
        .filter(
            (SystemUser.username == user_data.username)
            | (SystemUser.email == user_data.email)
        )
        .first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="用戶名或郵箱已存在")

    # 創建用戶
    password_hash = AuthService.get_password_hash(user_data.password)

    new_user = SystemUser(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.username,
        password_hash=password_hash,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        last_login=new_user.last_login,
        created_at=new_user.created_at,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_system_user(
    user_id: int,
    user_data: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """更新系統用戶 - 需要 user.edit 權限"""
    user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    # 更新用戶資訊
    update_data = user_data.dict(exclude_unset=True)

    # 如果有新密碼，進行雜湊處理
    if "password" in update_data:
        update_data["password_hash"] = AuthService.get_password_hash(
            update_data.pop("password")
        )

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
    )


@router.delete("/{user_id}")
async def delete_system_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """刪除系統用戶 - 需要 user.delete 權限"""
    user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    # 不能刪除自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能刪除自己的帳號")

    db.delete(user)
    db.commit()

    return {"message": "用戶已刪除"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """啟用用戶 - 需要 user.edit 權限"""
    user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    user.is_active = True
    db.commit()

    return {"message": "用戶已啟用"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """停用用戶 - 需要 user.edit 權限"""
    user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    # 不能停用自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能停用自己的帳號")

    user.is_active = False
    db.commit()

    return {"message": "用戶已停用"}
