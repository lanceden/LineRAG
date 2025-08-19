"""
公司邀請模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.core.database import Base
import uuid


class CompanyInvitation(Base):
    """公司邀請模型"""

    __tablename__ = "company_invitations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="邀請 ID")
    
    # 邀請資訊
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, comment="公司 ID")
    email = Column(String(255), nullable=False, comment="被邀請者郵箱")
    name = Column(String(255), nullable=False, comment="被邀請者姓名")
    role = Column(String(50), default="cs_agent", comment="角色")
    
    # 邀請狀態
    is_accepted = Column(Boolean, default=False, comment="是否已接受")
    is_expired = Column(Boolean, default=False, comment="是否已過期")
    
    # 邀請者資訊
    invited_by = Column(Integer, ForeignKey('system_users.id'), nullable=False, comment="邀請者 ID")
    
    # 時間資訊
    invited_at = Column(DateTime, default=datetime.utcnow, comment="邀請時間")
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7), comment="過期時間")
    accepted_at = Column(DateTime, comment="接受時間")
    
    # 邀請訊息
    message = Column(Text, comment="邀請訊息")
    
    # 關聯
    company = relationship("Company", backref="invitations")
    inviter = relationship("SystemUser", backref="sent_invitations")

    def __repr__(self):
        return f"<CompanyInvitation(id={self.id}, email='{self.email}', company_id={self.company_id})>"
    
    @property
    def is_valid(self):
        """檢查邀請是否有效"""
        return not self.is_accepted and not self.is_expired and datetime.utcnow() < self.expires_at
    
    def expire(self):
        """設定邀請為過期"""
        self.is_expired = True
    
    def accept(self):
        """接受邀請"""
        self.is_accepted = True
        self.accepted_at = datetime.utcnow()
