"""
公司管理服務
"""

import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.company import Company
from app.models.system_user import SystemUser
from app.models.permission import UserPermission
from app.models.invitation import CompanyInvitation
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyStats,
    CompanyListResponse,
    CompanyUserCreate,
    CompanyUserListResponse,
    BatchOperationRequest,
    BatchOperationResponse,
)
from app.core.exceptions import NotFoundError, ValidationError, PermissionError


class CompanyService:
    """公司管理服務 - 靜態方法模式"""

    @staticmethod
    def get_companies(
        db: Session,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> CompanyListResponse:
        """獲取公司列表"""

        query = db.query(Company)

        # 搜尋過濾
        if search:
            search_filter = or_(
                Company.name.ilike(f"%{search}%"),
                Company.code.ilike(f"%{search}%"),
                Company.description.ilike(f"%{search}%"),
                Company.email.ilike(f"%{search}%"),
            )
            query = query.filter(search_filter)

        # 狀態過濾
        if is_active is not None:
            query = query.filter(Company.is_active == is_active)

        # 排序
        if hasattr(Company, sort_by):
            order_column = getattr(Company, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        # 總數
        total = query.count()

        # 分頁
        offset = (page - 1) * limit
        companies = query.offset(offset).limit(limit).all()

        return CompanyListResponse(
            companies=companies,
            total=total,
            page=page,
            limit=limit,
            has_next=offset + limit < total,
            has_prev=page > 1,
        )

    @staticmethod
    def get_company(db: Session, company_id: int) -> Company:
        """獲取單個公司"""
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise NotFoundError(f"公司 ID {company_id} 不存在")
        return company

    @staticmethod
    def create_company(db: Session, company_data: CompanyCreate) -> Company:
        """建立新公司"""

        # 檢查公司代碼是否重複
        existing = db.query(Company).filter(Company.code == company_data.code).first()
        if existing:
            raise ValidationError(f"公司代碼 '{company_data.code}' 已存在")

        # 檢查公司名稱是否重複
        existing_name = (
            db.query(Company).filter(Company.name == company_data.name).first()
        )
        if existing_name:
            raise ValidationError(f"公司名稱 '{company_data.name}' 已存在")

        # 建立公司
        company = Company(**company_data.model_dump())

        # 設定 RAG 工作目錄
        if not company.rag_working_dir:
            company.rag_working_dir = f"/data/rag/{company.code}"

        db.add(company)
        db.commit()
        db.refresh(company)

        # 建立工作目錄
        CompanyService._create_company_directories(company)

        return company

    @staticmethod
    def update_company(
        db: Session, company_id: int, company_data: CompanyUpdate
    ) -> Company:
        """更新公司資訊"""
        company = CompanyService.get_company(db, company_id)

        # 更新欄位
        update_data = company_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)

        company.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(company)

        return company

    @staticmethod
    def delete_company(db: Session, company_id: int) -> bool:
        """刪除公司"""
        company = CompanyService.get_company(db, company_id)

        # 檢查是否有關聯資料 - 使用新的權限系統
        from app.models.permission import UserPermission

        user_permissions = (
            db.query(UserPermission)
            .filter(UserPermission.accessible_companies.any(str(company_id)))
            .count()
        )

        if user_permissions > 0:
            raise ValidationError("無法刪除有用戶的公司，請先移除所有用戶")

        # 軟刪除 (設為非活躍)
        company.is_active = False
        company.updated_at = datetime.utcnow()

        db.commit()

        return True

    @staticmethod
    def activate_company(db: Session, company_id: int) -> Company:
        """啟用公司"""
        company = CompanyService.get_company(db, company_id)
        company.is_active = True
        company.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(company)

        return company

    @staticmethod
    def deactivate_company(db: Session, company_id: int) -> Company:
        """停用公司"""
        company = CompanyService.get_company(db, company_id)
        company.is_active = False
        company.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(company)

        return company

    @staticmethod
    def get_company_stats(db: Session, company_id: int) -> CompanyStats:
        """獲取公司統計資訊"""
        company = CompanyService.get_company(db, company_id)

        # 用戶統計 - 使用新的權限系統
        from app.models.permission import UserPermission
        from app.models.system_user import SystemUser
        from sqlalchemy import and_

        user_permissions_with_company = (
            db.query(UserPermission)
            .filter(UserPermission.accessible_companies.any(str(company_id)))
            .all()
        )

        total_users = len(user_permissions_with_company)

        # 統計活躍用戶
        active_users = 0
        for up in user_permissions_with_company:
            user = (
                db.query(SystemUser)
                .filter(and_(SystemUser.id == up.user_id, SystemUser.is_active == True))
                .first()
            )
            if user:
                active_users += 1

        # 文檔統計 (如果有文檔表)
        total_documents = 0
        try:
            from app.models.document import DocumentMetadata

            total_documents = (
                db.query(DocumentMetadata)
                .filter(DocumentMetadata.company_id == company_id)
                .count()
            )
        except ImportError:
            pass

        # 對話統計 (暫時使用模擬資料)
        total_conversations = 0
        monthly_conversations = 0

        # 儲存統計
        storage_used = 0
        storage_limit = company.storage_quota_gb * 1024 * 1024 * 1024  # GB to bytes

        # 計算儲存使用量 (如果有檔案系統統計)
        if company.rag_working_dir and os.path.exists(company.rag_working_dir):
            try:
                storage_used = CompanyService._calculate_directory_size(
                    company.rag_working_dir
                )
            except:
                pass

        return CompanyStats(
            total_users=total_users,
            active_users=active_users,
            total_documents=total_documents,
            total_conversations=total_conversations,
            monthly_conversations=monthly_conversations,
            storage_used=storage_used,
            storage_limit=storage_limit,
            last_activity=company.updated_at,
        )

    @staticmethod
    def get_company_users(
        db: Session, company_id: int, page: int = 1, limit: int = 20
    ) -> CompanyUserListResponse:
        """獲取公司用戶列表"""
        # 驗證公司存在
        CompanyService.get_company(db, company_id)

        # 使用新的權限系統獲取有此公司存取權限的用戶
        from app.models.permission import UserPermission

        user_permissions_with_company = (
            db.query(UserPermission)
            .filter(UserPermission.accessible_companies.any(str(company_id)))
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        # 獲取總數
        total = (
            db.query(UserPermission)
            .filter(UserPermission.accessible_companies.any(str(company_id)))
            .count()
        )

        # 轉換為公司用戶格式
        from app.models.system_user import SystemUser

        company_users = []
        for user_perm in user_permissions_with_company:
            user = (
                db.query(SystemUser).filter(SystemUser.id == user_perm.user_id).first()
            )
            if user:
                company_users.append(
                    {
                        "id": user.id,
                        "email": user.email,
                        "name": user.full_name,
                        "role": "user",  # 簡化角色設定
                        "is_active": user.is_active,
                        "created_at": user.created_at,
                        "last_login": user.last_login,
                        "permissions": user_perm.granted_permissions or [],
                    }
                )

        return CompanyUserListResponse(
            users=company_users, total=total, page=page, limit=limit
        )

    @staticmethod
    def batch_operation(
        db: Session, request: BatchOperationRequest
    ) -> BatchOperationResponse:
        """批次操作公司"""
        success_count = 0
        failed_count = 0
        errors = []

        for company_id in request.company_ids:
            try:
                if request.operation == "activate":
                    CompanyService.activate_company(db, company_id)
                elif request.operation == "deactivate":
                    CompanyService.deactivate_company(db, company_id)
                elif request.operation == "delete":
                    CompanyService.delete_company(db, company_id)
                else:
                    raise ValidationError(f"不支援的操作: {request.operation}")

                success_count += 1

            except Exception as e:
                failed_count += 1
                errors.append({"company_id": company_id, "error": str(e)})

        return BatchOperationResponse(
            success=success_count,
            failed=failed_count,
            errors=errors if errors else None,
        )

    def invite_user(
        self, company_id: int, user_data: CompanyUserCreate, inviter_id: int
    ) -> CompanyInvitation:
        """邀請用戶加入公司"""
        company = self.get_company(company_id)

        # 檢查是否已經邀請過
        existing_invitation = (
            self.db.query(CompanyInvitation)
            .filter(
                and_(
                    CompanyInvitation.company_id == company_id,
                    CompanyInvitation.email == user_data.email,
                    CompanyInvitation.is_accepted == False,
                    CompanyInvitation.is_expired == False,
                )
            )
            .first()
        )

        if existing_invitation and existing_invitation.is_valid:
            raise ValidationError(f"已經邀請過 {user_data.email}，請等待回應")

        # 檢查用戶是否已經是公司成員
        existing_user = (
            self.db.query(SystemUser)
            .filter(SystemUser.email == user_data.email)
            .first()
        )
        if existing_user:
            # 檢查是否已經在公司中 - 使用新的權限系統
            user_permission = (
                self.db.query(UserPermission)
                .filter(
                    and_(
                        UserPermission.user_id == existing_user.id,
                        UserPermission.accessible_companies.any(company_id),
                    )
                )
                .first()
            )

            if user_permission:
                raise ValidationError(f"{user_data.email} 已經是公司成員")

        # 建立邀請
        invitation = CompanyInvitation(
            company_id=company_id,
            email=user_data.email,
            name=user_data.name,
            role=user_data.role,
            invited_by=inviter_id,
            message=f"邀請您加入 {company.name}",
        )

        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)

        # TODO: 發送邀請郵件

        return invitation

    @staticmethod
    def get_company_settings(db: Session, company_id: int) -> dict:
        """獲取公司設定"""
        company = CompanyService.get_company(db, company_id)

        return {
            "line_bot_enabled": company.line_bot_enabled,
            "line_channel_token": company.line_channel_token,
            "line_channel_secret": company.line_channel_secret,
            "subscription_plan": company.subscription_plan,
            "max_documents": company.max_documents,
            "max_queries_per_month": company.max_queries_per_month,
            "storage_quota_gb": company.storage_quota_gb,
            "auto_response_enabled": True,  # 預設值
            "business_hours": {
                "enabled": False,
                "timezone": "Asia/Taipei",
                "schedule": {},
            },
            "integrations": {
                "line": {"enabled": company.line_bot_enabled},
                "slack": {"enabled": False},
                "teams": {"enabled": False},
            },
        }

    @staticmethod
    def update_company_settings(db: Session, company_id: int, settings: dict) -> dict:
        """更新公司設定"""
        company = CompanyService.get_company(db, company_id)

        # 更新可設定的欄位
        if "line_bot_enabled" in settings:
            company.line_bot_enabled = settings["line_bot_enabled"]
        if "line_channel_token" in settings:
            company.line_channel_token = settings["line_channel_token"]
        if "line_channel_secret" in settings:
            company.line_channel_secret = settings["line_channel_secret"]
        if "subscription_plan" in settings:
            company.subscription_plan = settings["subscription_plan"]
        if "max_documents" in settings:
            company.max_documents = settings["max_documents"]
        if "max_queries_per_month" in settings:
            company.max_queries_per_month = settings["max_queries_per_month"]
        if "storage_quota_gb" in settings:
            company.storage_quota_gb = settings["storage_quota_gb"]

        company.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(company)

        return CompanyService.get_company_settings(db, company_id)

    @staticmethod
    def get_company_by_code(db: Session, company_code: str) -> Optional[Company]:
        """根據公司代碼獲取公司"""
        return (
            db.query(Company)
            .filter(Company.code == company_code, Company.is_active == True)
            .first()
        )

    @staticmethod
    def get_company_by_line_channel(
        db: Session, channel_token: str
    ) -> Optional[Company]:
        """根據 LINE Channel Token 獲取公司"""
        return (
            db.query(Company)
            .filter(
                Company.line_channel_token == channel_token,
                Company.is_active == True,
                Company.line_bot_enabled == True,
            )
            .first()
        )

    @staticmethod
    def update_line_settings(
        db: Session,
        company_id: int,
        channel_token: str,
        channel_secret: str,
        bot_enabled: bool = True,
    ) -> Company:
        """更新公司的 LINE 設定"""
        company = CompanyService.get_company(db, company_id)

        # 檢查 Channel Token 是否已被其他公司使用
        if channel_token:
            existing = (
                db.query(Company)
                .filter(
                    Company.line_channel_token == channel_token,
                    Company.id != company_id,
                )
                .first()
            )
            if existing:
                raise ValidationError(
                    f"LINE Channel Token 已被公司 '{existing.name}' 使用"
                )

        company.line_channel_token = channel_token
        company.line_channel_secret = channel_secret
        company.line_bot_enabled = bot_enabled
        company.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(company)
        return company

    @staticmethod
    def _create_company_directories(company: Company):
        """建立公司相關目錄"""
        import os

        if company.rag_working_dir:
            try:
                os.makedirs(company.rag_working_dir, exist_ok=True)
                os.makedirs(f"{company.rag_working_dir}/documents", exist_ok=True)
                os.makedirs(f"{company.rag_working_dir}/vectors", exist_ok=True)
                os.makedirs(f"{company.rag_working_dir}/temp", exist_ok=True)
            except Exception as e:
                print(f"建立目錄失敗: {e}")

    @staticmethod
    def _calculate_directory_size(directory: str) -> int:
        """計算目錄大小"""
        import os

        total_size = 0
        try:
            for dirpath, _, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size
