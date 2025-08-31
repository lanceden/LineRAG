import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.multitenant_rag import get_multitenant_rag_service
from app.services.ingestion_service import get_ingestion_service
from app.utils.audit_helper import create_audit


async def process_folder_task(
    batch_id: str, folder_path: str, company_id: int, user_id: int
):
    """背景批次資料夾處理任務"""
    print(
        f"[folder_task] 開始處理 folder batch={batch_id} path={folder_path} company={company_id} user={user_id}"
    )
    db: Session = SessionLocal()
    try:
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(company_id, db)
        result = await rag_service.process_folder(folder_path, company_id)
        ingestion_service = get_ingestion_service(db)
        processed = (
            result.get("processed_files", []) if isinstance(result, dict) else []
        )
        if result.get("status") == "success" and processed:
            import mimetypes

            for f in processed:
                try:
                    ingestion_service.create_document(
                        document_id=str(uuid.uuid4()),
                        original_filename=f.get("filename"),
                        stored_path=f.get("path"),
                        size=f.get("size", 0),
                        mime=mimetypes.guess_type(f.get("filename"))[0]
                        or Path(f.get("filename")).suffix.lower(),
                        company_id=company_id,
                        created_by=str(user_id),
                        status="completed",
                    )
                except Exception as per_err:
                    print(f"[folder_task] 建立文檔記錄失敗 {per_err}")
            create_audit(
                db,
                company_id=company_id,
                tenant_user_id=user_id,
                action="folder_ingest",
                resource_type="folder",
                resource_id=batch_id,
                endpoint="/ingest/folder",
                method="POST",
                status="success",
                request_data={"folder": folder_path, "files": len(processed)},
            )
        else:
            create_audit(
                db,
                company_id=company_id,
                tenant_user_id=user_id,
                action="folder_ingest",
                resource_type="folder",
                resource_id=batch_id,
                endpoint="/ingest/folder",
                method="POST",
                status="failed",
                error_message=result.get("message", "unknown error"),
            )
    except Exception as e:
        print(f"[folder_task] 批次處理失敗: {e}")
        create_audit(
            db,
            company_id=company_id,
            tenant_user_id=user_id,
            action="folder_ingest",
            resource_type="folder",
            resource_id=batch_id,
            endpoint="/ingest/folder",
            method="POST",
            status="failed",
            error_message=str(e),
        )
    finally:
        try:
            db.close()
        except:
            pass
