"""
系統管理員用戶模型（Web登入用）
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# 用戶-公司權限關聯表
user_company_access = Table(
    'user_company_access', Base.metadata,
    Column('system_user_id', Integer, ForeignKey('system_users.id'), primary_key=True),
    Column('company_id', Integer, ForeignKey('companies.id'), primary_key=True),
    Column('permission_level', String(20), default='read_write', comment='權限級別: read, read_write, admin')
)


class SystemUser(Base):
    """系統管理員用戶模型（Web登入用）"""

    __tablename__ = "system_users"

    id = Column(Integer, primary_key=True, index=True)
    
    # 登入資訊
    username = Column(String(50), unique=True, nullable=False, comment="登入帳號")
    email = Column(String(255), unique=True, nullable=False, comment="電子郵件")
    password_hash = Column(String(255), nullable=False, comment="密碼雜湊")
    
    # 個人資訊
    full_name = Column(String(255), nullable=False, comment="姓名")
    
    # 系統角色
    role = Column(String(50), default="admin", comment="系統角色: super_admin, admin")
    
    # 狀態管理
    is_active = Column(Boolean, default=True, comment="是否啟用")
    last_login = Column(DateTime, comment="最後登入時間")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯 - 可管理的公司（多對多關係）
    accessible_companies = relationship(
        "Company", 
        secondary=user_company_access, 
        back_populates="system_users"
    )

    def __repr__(self):
        return f"<SystemUser(id={self.id}, username='{self.username}', role='{self.role}')>"

    @property
    def is_super_admin(self):
        return self.role == "super_admin"

    @property
    def is_admin(self):
        return self.role in ["super_admin", "admin"]
    
    def can_manage_company(self, company_id: int) -> bool:
        """檢查是否有權限管理指定公司"""
        if self.is_super_admin:
            return True
        return any(company.id == company_id for company in self.accessible_companies)