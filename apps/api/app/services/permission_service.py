"""
權限管理服務
基於 PERMISSION_SYSTEM_DESIGN.md 設計
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.permission import Permission, UserPermission
from app.models.system_user import SystemUser
from app.models.company import Company


class PermissionService:
    """權限管理服務"""

    @staticmethod
    def create_permission(
        db: Session,
        code: str,
        name: str,
        description: str = None,
        category: str = "功能權限",
        is_active: bool = True,
    ) -> Permission:
        """創建新權限"""
        permission = Permission(
            code=code,
            name=name,
            description=description,
            category=category,
            is_active=is_active,
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission

    @staticmethod
    def get_all_permissions(
        db: Session, category: Optional[str] = None, is_active: Optional[bool] = None
    ) -> List[Permission]:
        """獲取所有權限"""
        query = db.query(Permission)

        if category:
            query = query.filter(Permission.category == category)
        if is_active is not None:
            query = query.filter(Permission.is_active == is_active)

        return query.order_by(Permission.category, Permission.code).all()

    @staticmethod
    def get_permission_by_code(db: Session, code: str) -> Optional[Permission]:
        """根據代碼獲取權限"""
        return db.query(Permission).filter(Permission.code == code).first()

    @staticmethod
    def update_permission(
        db: Session,
        permission_id: int,
        name: str = None,
        description: str = None,
        category: str = None,
        is_active: bool = None,
    ) -> Optional[Permission]:
        """更新權限"""
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            return None

        if name is not None:
            permission.name = name
        if description is not None:
            permission.description = description
        if category is not None:
            permission.category = category
        if is_active is not None:
            permission.is_active = is_active

        db.commit()
        db.refresh(permission)
        return permission

    @staticmethod
    def delete_permission(db: Session, permission_id: int) -> bool:
        """刪除權限"""
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            return False

        db.delete(permission)
        db.commit()
        return True

    @staticmethod
    def get_user_permissions(db: Session, user_id: int) -> Optional[UserPermission]:
        """獲取用戶權限"""
        return (
            db.query(UserPermission).filter(UserPermission.user_id == user_id).first()
        )

    @staticmethod
    def set_user_permissions(
        db: Session, user_id: int, permission_codes: List[str], company_ids: List[int]
    ) -> UserPermission:
        """設置用戶權限"""
        # 檢查用戶是否存在
        user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # 驗證權限代碼
        valid_permissions = (
            db.query(Permission.code)
            .filter(
                and_(
                    Permission.code.in_(permission_codes), Permission.is_active == True
                )
            )
            .all()
        )
        valid_permission_codes = [p.code for p in valid_permissions]

        # 驗證公司 ID
        valid_companies = (
            db.query(Company.id)
            .filter(and_(Company.id.in_(company_ids), Company.is_active == True))
            .all()
        )
        valid_company_ids = [c.id for c in valid_companies]

        # 檢查是否已有用戶權限記錄
        user_permission = (
            db.query(UserPermission).filter(UserPermission.user_id == user_id).first()
        )

        if user_permission:
            # 更新現有記錄
            user_permission.granted_permissions = valid_permission_codes
            user_permission.accessible_companies = valid_company_ids
        else:
            # 創建新記錄
            user_permission = UserPermission(
                user_id=user_id,
                granted_permissions=valid_permission_codes,
                accessible_companies=valid_company_ids,
            )
            db.add(user_permission)

        db.commit()
        db.refresh(user_permission)
        return user_permission

    @staticmethod
    def add_user_permission(
        db: Session, user_id: int, permission_code: str
    ) -> UserPermission:
        """為用戶添加單個權限"""
        user_permission = (
            db.query(UserPermission).filter(UserPermission.user_id == user_id).first()
        )

        if not user_permission:
            user_permission = UserPermission(
                user_id=user_id,
                granted_permissions=[permission_code],
                accessible_companies=[],
            )
            db.add(user_permission)
        else:
            if not user_permission.granted_permissions:
                user_permission.granted_permissions = []

            if permission_code not in user_permission.granted_permissions:
                user_permission.granted_permissions.append(permission_code)

        db.commit()
        db.refresh(user_permission)
        return user_permission

    @staticmethod
    def remove_user_permission(
        db: Session, user_id: int, permission_code: str
    ) -> Optional[UserPermission]:
        """移除用戶的單個權限"""
        user_permission = (
            db.query(UserPermission).filter(UserPermission.user_id == user_id).first()
        )

        if not user_permission or not user_permission.granted_permissions:
            return None

        if permission_code in user_permission.granted_permissions:
            user_permission.granted_permissions.remove(permission_code)
            db.commit()
            db.refresh(user_permission)

        return user_permission

    @staticmethod
    def add_user_company_access(
        db: Session, user_id: int, company_id: int
    ) -> UserPermission:
        """為用戶添加公司存取權限"""
        user_permission = (
            db.query(UserPermission).filter(UserPermission.user_id == user_id).first()
        )

        if not user_permission:
            user_permission = UserPermission(
                user_id=user_id,
                granted_permissions=[],
                accessible_companies=[company_id],
            )
            db.add(user_permission)
        else:
            if not user_permission.accessible_companies:
                user_permission.accessible_companies = []

            if company_id not in user_permission.accessible_companies:
                user_permission.accessible_companies.append(company_id)

        db.commit()
        db.refresh(user_permission)
        return user_permission

    @staticmethod
    def remove_user_company_access(
        db: Session, user_id: int, company_id: int
    ) -> Optional[UserPermission]:
        """移除用戶的公司存取權限"""
        user_permission = (
            db.query(UserPermission).filter(UserPermission.user_id == user_id).first()
        )

        if not user_permission or not user_permission.accessible_companies:
            return None

        if company_id in user_permission.accessible_companies:
            user_permission.accessible_companies.remove(company_id)
            db.commit()
            db.refresh(user_permission)

        return user_permission

    @staticmethod
    def remove_user_permissions(db: Session, user_id: int) -> bool:
        """移除用戶的所有權限"""
        user_permission = (
            db.query(UserPermission).filter(UserPermission.user_id == user_id).first()
        )
        
        if user_permission:
            db.delete(user_permission)
            db.commit()
            return True
        return False

    @staticmethod
    def get_users_with_permission(
        db: Session, permission_code: str
    ) -> List[SystemUser]:
        """獲取擁有指定權限的所有用戶"""
        user_permissions = (
            db.query(UserPermission)
            .filter(UserPermission.granted_permissions.any(permission_code))
            .all()
        )

        user_ids = [up.user_id for up in user_permissions]

        return (
            db.query(SystemUser)
            .filter(and_(SystemUser.id.in_(user_ids), SystemUser.is_active == True))
            .all()
        )

    @staticmethod
    def get_users_with_company_access(db: Session, company_id: int) -> List[SystemUser]:
        """獲取可存取指定公司的所有用戶"""
        user_permissions = (
            db.query(UserPermission)
            .filter(UserPermission.accessible_companies.any(company_id))
            .all()
        )

        user_ids = [up.user_id for up in user_permissions]

        return (
            db.query(SystemUser)
            .filter(and_(SystemUser.id.in_(user_ids), SystemUser.is_active == True))
            .all()
        )
