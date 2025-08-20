"""
公司（租戶）模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Company(Base):
    """公司/租戶模型"""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="公司名稱")
    code = Column(String(50), unique=True, nullable=False, comment="公司代碼")

    # 基本資訊
    description = Column(Text, comment="公司描述")
    website = Column(String(255), comment="公司網站")
    phone = Column(String(50), comment="聯絡電話")
    email = Column(String(255), comment="聯絡信箱")
    address = Column(Text, comment="公司地址")
    logo_url = Column(String(500), comment="公司 Logo URL")

    # LINE Channel 設定
    line_channel_token = Column(Text, comment="LINE Channel Access Token")
    line_channel_secret = Column(String(255), comment="LINE Channel Secret")
    line_bot_enabled = Column(Boolean, default=True, comment="LINE 機器人是否啟用")

    # 訂閱設定
    subscription_plan = Column(String(50), default="standard", comment="訂閱方案")
    max_documents = Column(Integer, default=1000, comment="最大文檔數量")
    max_queries_per_month = Column(Integer, default=10000, comment="每月查詢上限")

    # 系統設定
    storage_quota_gb = Column(Integer, default=10, comment="儲存配額(GB)")

    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, comment="是否啟用")

    # 關聯
    tenant_users = relationship("TenantUser", back_populates="company")
    documents = relationship("DocumentMetadata", back_populates="company")
    audit_logs = relationship("AuditLog", back_populates="company")

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', code='{self.code}')>"
