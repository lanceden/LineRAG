"""
審計日誌模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class AuditLog(Base):
    """審計日誌模型"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(
        Integer, ForeignKey("companies.id"), nullable=False, comment="所屬公司ID"
    )
    tenant_user_id = Column(Integer, ForeignKey("tenant_users.id"), comment="租戶用戶ID")
    system_user_id = Column(Integer, ForeignKey("system_users.id"), comment="系統用戶ID")

    # 操作資訊
    action = Column(
        String(100), nullable=False, comment="操作類型: query, upload, delete, login等"
    )
    resource_type = Column(String(50), comment="資源類型: document, user, system等")
    resource_id = Column(String(255), comment="資源ID")

    # 請求資訊
    endpoint = Column(String(255), comment="API端點")
    method = Column(String(10), comment="HTTP方法")
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用戶代理")

    # 結果資訊
    status = Column(String(20), comment="操作狀態: success, failed, error")
    response_time_ms = Column(Integer, comment="回應時間(毫秒)")
    error_code = Column(String(50), comment="錯誤代碼")
    error_message = Column(Text, comment="錯誤訊息")

    # 詳細資訊
    request_data = Column(JSON, comment="請求資料")
    response_data = Column(JSON, comment="回應資料")
    extra_data = Column(JSON, comment="額外元資料")

    # 時間戳記
    timestamp = Column(
        DateTime, default=datetime.utcnow, index=True, comment="操作時間"
    )

    # 關聯
    company = relationship("Company", back_populates="audit_logs")
    tenant_user = relationship("TenantUser", back_populates="audit_logs")
    system_user = relationship("SystemUser")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', company_id={self.company_id}, timestamp={self.timestamp})>"
