from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.multitenant_rag import get_multitenant_rag_service
from app.services.ingestion_service import get_ingestion_service
from app.utils.audit_helper import create_audit


async def process_content_task(
    task_id: str,
    company_id: int,
    user_id: int,
    content_list,
    file_path: str | None,
):
    """背景直接內容插入任務"""
    print(f"[content_task] 開始 content 任務 task={task_id} company={company_id}")
    db: Session = SessionLocal()
    ingestion_service = get_ingestion_service(db)
    try:
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(company_id, db)
        result = await rag_service.insert_content_list(
            content_list=content_list, file_path=file_path, company_id=company_id
        )
        if result.get("status") == "success":
            doc = ingestion_service.create_document(
                document_id=task_id,
                original_filename=(Path(file_path).name if file_path else "直接內容"),
                stored_path=file_path or "",
                size=len(str(content_list)),
                mime="content",
                company_id=company_id,
                created_by=str(user_id),
                status="completed",
            )
            create_audit(
                db,
                company_id=company_id,
                tenant_user_id=user_id,
                action="content_ingest",
                resource_type="document",
                resource_id=doc.document_id,
                endpoint="/ingest/content",
                method="POST",
                status="success",
                request_data={"content_items": len(content_list)},
            )
        else:
            create_audit(
                db,
                company_id=company_id,
                tenant_user_id=user_id,
                action="content_ingest",
                resource_type="document",
                resource_id=task_id,
                endpoint="/ingest/content",
                method="POST",
                status="failed",
                error_message=result.get("message", "unknown error"),
            )
    except Exception as e:
        ingestion_service.create_document(
            document_id=task_id,
            original_filename=(Path(file_path).name if file_path else "直接內容"),
            stored_path=file_path or "",
            size=len(str(content_list)),
            mime="content",
            company_id=company_id,
            created_by=str(user_id),
            status="failed",
            error=str(e),
        )
        create_audit(
            db,
            company_id=company_id,
            tenant_user_id=user_id,
            action="content_ingest",
            resource_type="document",
            resource_id=task_id,
            endpoint="/ingest/content",
            method="POST",
            status="failed",
            error_message=str(e),
        )
    finally:
        try:
            db.close()
        except:
            pass
