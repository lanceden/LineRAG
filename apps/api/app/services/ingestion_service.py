from sqlalchemy.orm import Session
from app.models.document import DocumentMetadata
from app.models.audit import AuditLog
from datetime import datetime


class IngestionService:
    def __init__(self, db: Session):
        self.db = db

    def create_pending_document(
        self,
        *,
        document_id: str,
        original_filename: str,
        stored_path: str,
        size: int,
        mime: str,
        company_id: int,
        created_by: str,
    ) -> DocumentMetadata:
        doc = DocumentMetadata(
            document_id=document_id,
            original_filename=original_filename,
            file_path=stored_path,
            file_size=size,
            mime_type=mime,
            company_id=company_id,
            created_by=created_by,
            processing_status="pending",
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def create_document(
        self,
        *,
        document_id: str,
        original_filename: str,
        stored_path: str,
        size: int,
        mime: str,
        company_id: int,
        created_by: str,
        status: str = "completed",
        error: str | None = None,
    ) -> DocumentMetadata:
        """Generic creator with custom status (e.g. for folder/content ingestion)."""
        doc = DocumentMetadata(
            document_id=document_id,
            original_filename=original_filename,
            file_path=stored_path,
            file_size=size,
            mime_type=mime,
            company_id=company_id,
            created_by=created_by,
            processing_status=status,
            error_message=error,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def log_upload_audit(
        self, *, company_id: int, system_user_id: int, doc: DocumentMetadata
    ):
        audit = AuditLog(
            company_id=company_id,
            system_user_id=system_user_id,
            action="document_upload",
            resource_type="document",
            resource_id=doc.document_id,
            endpoint="/ingest/document",
            method="POST",
            status="success",
            request_data={
                "filename": doc.original_filename,
                "size": doc.file_size,
                "mime": doc.mime_type,
            },
        )
        self.db.add(audit)
        self.db.commit()

    def mark_failed(self, doc: DocumentMetadata, error: str):
        doc.processing_status = "failed"
        doc.error_message = error
        self.db.commit()

    def mark_completed(
        self, doc: DocumentMetadata, lightrag_doc_id: str, file_size: int = None
    ):
        doc.processing_status = "completed"
        doc.lightrag_doc_id = lightrag_doc_id
        if file_size:
            doc.file_size = file_size
        self.db.commit()


def get_ingestion_service(db: Session) -> IngestionService:
    return IngestionService(db)
