"""
系統管理員用戶模型（Web登入用）
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base


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

    # 狀態管理
    is_active = Column(Boolean, default=True, comment="是否啟用")
    last_login = Column(DateTime, comment="最後登入時間")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # 關聯關係 - 一對一權限系統
    permissions = relationship(
        "UserPermission",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<SystemUser(id={self.id}, username='{self.username}')>"
