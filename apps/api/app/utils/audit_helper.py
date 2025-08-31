from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def create_audit(
    db: Session,
    *,
    company_id: int,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    endpoint: str | None = None,
    method: str | None = None,
    status: str,
    tenant_user_id: int | None = None,
    system_user_id: int | None = None,
    error_message: str | None = None,
    request_data: Dict[str, Any] | None = None,
    response_data: Dict[str, Any] | None = None,
    extra_data: Dict[str, Any] | None = None,
) -> AuditLog:
    audit = AuditLog(
        company_id=company_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
        status=status,
        tenant_user_id=tenant_user_id,
        system_user_id=system_user_id,
        error_message=error_message,
        request_data=request_data,
        response_data=response_data,
        extra_data=extra_data,
    )
    db.add(audit)
    db.commit()
    return audit
