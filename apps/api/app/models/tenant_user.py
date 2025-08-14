"""
租戶用戶模型（LINE Bot用戶）
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class TenantUser(Base):
    """租戶用戶模型（LINE Bot用戶）"""

    __tablename__ = "tenant_users"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(
        Integer, ForeignKey("companies.id"), nullable=False, comment="所屬公司ID"
    )

    # LINE 用戶資訊
    line_id = Column(String(255), nullable=False, index=True, comment="LINE 用戶ID")
    line_display_name = Column(String(255), comment="LINE 顯示名稱")

    # 系統用戶資訊
    name = Column(String(255), nullable=False, comment="用戶姓名")
    email = Column(String(255), comment="電子郵件")
    role = Column(String(50), default="user", comment="角色: admin, cs, user")

    # 狀態管理
    is_active = Column(Boolean, default=True, comment="是否啟用")
    last_login = Column(DateTime, comment="最後登入時間")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 統計資訊
    total_queries = Column(Integer, default=0, comment="總查詢次數")
    monthly_queries = Column(Integer, default=0, comment="當月查詢次數")

    # 關聯
    company = relationship("Company", back_populates="tenant_users")
    audit_logs = relationship("AuditLog", back_populates="tenant_user")

    def __repr__(self):
        return f"<TenantUser(id={self.id}, line_id='{self.line_id}', name='{self.name}', company_id={self.company_id})>"

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_cs(self):
        return self.role == "cs"
