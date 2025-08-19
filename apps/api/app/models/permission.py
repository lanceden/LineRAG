"""
權限系統相關資料模型 - 根據 PERMISSION_SYSTEM_DESIGN.md
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from app.core.database import Base


class UserPermission(Base):
    """用戶權限配置表 - 一對一關係"""
    
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, 
        ForeignKey("system_users.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )
    granted_permissions = Column(
        ARRAY(String), 
        nullable=False, 
        default=[], 
        comment="授予的功能權限代碼列表"
    )
    accessible_companies = Column(
        ARRAY(String),
        nullable=False,
        default=[],
        comment="可存取的公司ID列表，['*']表示全部",
    )
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP, 
        server_default=func.current_timestamp(), 
        onupdate=func.current_timestamp()
    )

    # 關聯關係
    user = relationship("SystemUser", back_populates="permissions")


class Permission(Base):
    """權限定義表 - 簡單的功能權限"""
    
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, comment="權限代碼")
    name = Column(String(100), nullable=False, comment="權限名稱")
    category = Column(String(50), nullable=False, comment="功能分類")
    description = Column(Text, nullable=True, comment="權限描述")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否啟用")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP, 
        server_default=func.current_timestamp(), 
        onupdate=func.current_timestamp()
    )