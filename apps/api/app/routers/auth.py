"""
認證相關 API 路由
包含登入、登出、token 刷新等不需要認證的端點
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.auth import authenticate_user, AuthService
from app.models.system_user import SystemUser
from app.models.company import Company
from app.models.permission import UserPermission
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserInfo,
    CompanyInfo,
)

router = APIRouter(prefix="/auth", tags=["認證"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """系統管理員登入"""
    # 驗證用戶
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="帳號或密碼錯誤"
        )

    # 載入用戶權限資訊
    user_permission = (
        db.query(UserPermission).filter(UserPermission.user_id == user.id).first()
    )

    user_permissions = (
        user_permission.granted_permissions
        if user_permission and user_permission.granted_permissions
        else []
    )
    user_company_access = (
        user_permission.accessible_companies
        if user_permission and user_permission.accessible_companies
        else []
    )

    # 生成 JWT tokens（包含權限資訊以供緩存）
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "permissions": user_permissions,
        "company_access": user_company_access,
        "last_permission_check": datetime.utcnow().timestamp(),
    }
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
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
    )

    # 準備可訪問的公司列表（基於權限設定）
    accessible_companies = []
    if "*" in user_company_access:
        # 所有公司
        companies = db.query(Company).filter(Company.is_active == True).all()
        accessible_companies = [
            CompanyInfo(
                id=company.id,
                name=company.name,
                code=company.code,
                is_active=company.is_active,
            )
            for company in companies
        ]
    else:
        # 特定公司
        company_ids = [int(id) for id in user_company_access if id.isdigit()]
        if company_ids:
            companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
            accessible_companies = [
                CompanyInfo(
                    id=company.id,
                    name=company.name,
                    code=company.code,
                    is_active=company.is_active,
                )
                for company in companies
            ]

    return LoginResponse(
        success=True,
        message="登入成功",
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_info,
        accessible_companies=accessible_companies,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """刷新 access token"""
    try:
        # 驗證 refresh token
        payload = AuthService.verify_token(
            request.refresh_token, expected_type="refresh"
        )
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # 檢查用戶是否存在且活躍
        user = (
            db.query(SystemUser)
            .filter(SystemUser.id == user_id, SystemUser.is_active == True)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # 載入用戶權限資訊
        user_permission = (
            db.query(UserPermission).filter(UserPermission.user_id == user.id).first()
        )

        user_permissions = (
            user_permission.granted_permissions
            if user_permission and user_permission.granted_permissions
            else []
        )
        user_company_access = (
            user_permission.accessible_companies
            if user_permission and user_permission.accessible_companies
            else []
        )

        # 生成新的 access token（包含最新權限資訊）
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "permissions": user_permissions,
            "company_access": user_company_access,
            "last_permission_check": datetime.utcnow().timestamp(),
        }
        new_access_token = AuthService.create_access_token(token_data)

        return TokenResponse(access_token=new_access_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout():
    """登出 (客戶端應該清除 token)"""
    return {"success": True, "message": "登出成功"}


@router.post("/validate-token")
async def validate_token(token: str, db: Session = Depends(get_db)):
    """驗證 token 有效性"""
    try:
        payload = AuthService.verify_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # 檢查用戶是否存在且活躍
        user = (
            db.query(SystemUser)
            .filter(SystemUser.id == user_id, SystemUser.is_active == True)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return {
            "valid": True,
            "user_id": user.id,
            "username": user.username,
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )