"""
多租戶用戶管理服務
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from app.models.company import Company
from app.models.tenant_user import TenantUser
from app.models.audit import AuditLog


class MultiTenantUserService:
    """多租戶用戶管理服務"""

    def __init__(self, db: Session):
        self.db = db

    async def get_user_by_line_id(
        self, line_id: str, company_id: int = None
    ) -> Optional[TenantUser]:
        """根據 LINE ID 取得用戶"""
        query = self.db.query(TenantUser).filter(TenantUser.line_id == line_id)

        if company_id:
            query = query.filter(TenantUser.company_id == company_id)

        return query.first()

    async def get_user_company(
        self, line_id: str
    ) -> Optional[tuple[TenantUser, Company]]:
        """取得用戶及其所屬公司"""
        result = (
            self.db.query(TenantUser, Company)
            .join(Company, TenantUser.company_id == Company.id)
            .filter(
                TenantUser.line_id == line_id,
                TenantUser.is_active == True,
                Company.is_active == True,
            )
            .first()
        )

        return result if result else None

    async def create_user(
        self,
        company_id: int,
        line_id: str,
        name: str,
        role: str = "user",
        email: str = None,
        line_display_name: str = None,
    ) -> TenantUser:
        """建立新用戶"""
        user = TenantUser(
            company_id=company_id,
            line_id=line_id,
            name=name,
            role=role,
            email=email,
            line_display_name=line_display_name,
            created_at=datetime.utcnow(),
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # 記錄審計日誌
        await self.log_audit(
            company_id=company_id,
            user_id=user.id,
            action="user_created",
            resource_type="user",
            resource_id=str(user.id),
            status="success",
        )

        return user

    async def update_user_login(self, user_id: int):
        """更新用戶登入時間"""
        user = self.db.query(TenantUser).filter(TenantUser.id == user_id).first()
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()

    async def increment_user_queries(self, user_id: int):
        """增加用戶查詢次數"""
        user = self.db.query(TenantUser).filter(TenantUser.id == user_id).first()
        if user:
            user.total_queries += 1
            user.monthly_queries += 1
            self.db.commit()

    async def get_company_users(self, company_id: int) -> List[TenantUser]:
        """取得公司所有用戶"""
        return (
            self.db.query(TenantUser)
            .filter(TenantUser.company_id == company_id, TenantUser.is_active == True)
            .all()
        )

    async def check_user_permission(self, user_id: int, required_role: str) -> bool:
        """檢查用戶權限"""
        user = self.db.query(TenantUser).filter(TenantUser.id == user_id).first()
        if not user:
            return False

        role_hierarchy = {"user": 1, "cs": 2, "admin": 3}

        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 999)

        return user_level >= required_level

    async def log_audit(
        self,
        company_id: int,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        user_id: int = None,
        status: str = "success",
        ip_address: str = None,
        user_agent: str = None,
        endpoint: str = None,
        method: str = None,
        response_time_ms: int = None,
        error_message: str = None,
        metadata: dict = None,
    ):
        """記錄審計日誌"""
        audit_log = AuditLog(
            company_id=company_id,
            tenant_user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time_ms,
            error_message=error_message,
            metadata=metadata,
            timestamp=datetime.utcnow(),
        )

        self.db.add(audit_log)
        self.db.commit()


def get_user_service(db: Session) -> MultiTenantUserService:
    """取得用戶服務實例"""
    return MultiTenantUserService(db)


def get_multitenant_user_service(db: Session) -> MultiTenantUserService:
    """取得多租戶用戶服務實例"""
    return MultiTenantUserService(db)
