"""Document ingestion API routes"""

import os
import uuid
import logging
from pathlib import Path
from datetime import datetime
from fastapi import (
    APIRouter,
    BackgroundTasks,
    UploadFile,
    File,
    Form,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.middleware import get_current_user
from app.models.system_user import SystemUser
from app.models.document import DocumentMetadata
from app.schemas.ingest import IngestResponse, IngestRequest
from app.services.ingestion_service import IngestionService
from app.services.document_lifecycle_manager import (
    DocumentLifecycleManager,
    get_document_lifecycle_manager,
)
from app.utils.file_storage import (
    validate_extension,
    generate_doc_id_and_unique_name,
    write_file_bytes,
)
from app.utils.audit_helper import create_audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["ingest"])


@router.post("/ingest/document", response_model=IngestResponse)
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """Upload and process a single document - using true multithreading"""
    try:
        # Validate file extension
        if not validate_extension(file.filename):
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Generate unique filename
        doc_id, unique_filename = generate_doc_id_and_unique_name(file.filename)

        # Save file to company-specific upload directory
        temp_dir = Path(f"./uploads/company_{company_id}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = temp_dir / unique_filename

        # Write file content
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # 1. 立即創建資料庫記錄
        doc_metadata = DocumentMetadata(
            document_id=doc_id,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=len(content),
            mime_type=file.content_type or "application/octet-stream",
            company_id=company_id,
            created_by=current_user.username,
            processing_status="uploaded",  # 初始狀態
            uploaded_at=datetime.now(),
        )
        
        db.add(doc_metadata)
        db.commit()
        db.refresh(doc_metadata)
        
        logger.info(f"文檔記錄已創建: {doc_id}")

        # 2. 使用 FastAPI BackgroundTasks 處理
        task_id = str(uuid.uuid4())
        
        lifecycle_manager = get_document_lifecycle_manager()
        background_tasks.add_task(
            lifecycle_manager._process_document_async,
            task_id=task_id,
            file_path=str(file_path),
            company_id=company_id,
            user_id=current_user.username,
            original_filename=file.filename,
            document_id=doc_id,
        )

        logger.info(f"後台任務已提交: {task_id} (文檔: {doc_id})")

        # 3. 立即返回任務ID，讓前端可以輪詢狀態
        return IngestResponse(
            success=True,
            message="文檔已上傳並創建記錄，正在後台處理...",
            document_id=doc_id,
            task_id=task_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Document processing failed: {str(e)}"
        )


@router.post("/ingest/content", response_model=IngestResponse)
async def ingest_content(
    request: IngestRequest,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """Directly insert content list - supports pre-parsed multimodal content"""
    try:
        # Initialize services
        ingestion_service = IngestionService(db)

        # Process content
        result = await ingestion_service.insert_content_list(
            content_list=request.content_list,
            file_path=request.file_path or "content_list",
            company_id=request.company_id,
        )

        if result["status"] == "success":
            return IngestResponse(
                success=True,
                message=result["message"],
                document_id=f"content-{uuid.uuid4().hex[:16]}",
                task_id=str(uuid.uuid4()),
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Content ingestion failed: {str(e)}"
        )


@router.get("/ingest/status/{task_id}")
async def get_ingestion_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """Check ingestion task status"""
    try:
        lifecycle_manager = get_document_lifecycle_manager()
        status = lifecycle_manager.get_processing_status(task_id)

        return {
            "task_id": task_id,
            "status": status.get("status", "unknown"),
            "message": status.get("message", ""),
            "progress": status.get("progress", 0),
            "result": status,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/ingest/documents/{company_id}")
async def list_company_documents(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """List all documents for a company"""
    try:
        # Query documents
        documents = (
            db.query(DocumentMetadata)
            .filter(
                DocumentMetadata.company_id == company_id,
                DocumentMetadata.processing_status != "deleted",
            )
            .all()
        )

        return {
            "company_id": company_id,
            "documents": [
                {
                    "document_id": doc.document_id,
                    "original_filename": doc.original_filename,
                    "file_path": doc.file_path,
                    "file_size": doc.file_size,
                    "mime_type": doc.mime_type,
                    "company_id": doc.company_id,
                    "created_by": doc.created_by,
                    "processing_status": doc.processing_status,
                    "error_message": doc.error_message,
                    "created_at": (
                        doc.uploaded_at.isoformat() if doc.uploaded_at else None
                    ),
                    "updated_at": (
                        doc.processed_at.isoformat() if doc.processed_at else None
                    ),
                }
                for doc in documents
            ],
            "total_count": len(documents),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Document listing failed: {str(e)}"
        )


@router.delete("/ingest/documents/{company_id}/{document_id}")
async def delete_document(
    company_id: int,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """Delete document and related data"""
    try:
        lifecycle_manager = get_document_lifecycle_manager()

        result = await lifecycle_manager.delete_document(
            doc_id=document_id,
            company_id=company_id,
            user_id=current_user.username,
            db=db,
        )

        if result["status"] == "success":
            return {
                "success": True,
                "message": result["message"],
                "document_id": document_id,
                "freed_space_mb": result.get("freed_space_mb", 0),
            }
        else:
            raise HTTPException(status_code=404, detail=result["message"])

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Document deletion failed: {str(e)}"
        )


@router.get("/ingest/documents/{company_id}/{document_id}")
async def get_document_details(
    company_id: int,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """Get single document detailed status (with multimodal and raw status JSON)"""
    try:
        # Query document
        query = db.query(DocumentMetadata).filter(
            DocumentMetadata.company_id == company_id
        )

        if document_id.isdigit():
            doc = query.filter(DocumentMetadata.id == int(document_id)).first()
        else:
            doc = query.filter(DocumentMetadata.document_id == document_id).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "document_id": doc.document_id,
            "original_filename": doc.original_filename,
            "file_path": doc.file_path,
            "file_size": doc.file_size,
            "mime_type": doc.mime_type,
            "processing_status": doc.processing_status,
            "error_message": doc.error_message,
            "created_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "updated_at": doc.processed_at.isoformat() if doc.processed_at else None,
            "deleted_at": doc.deleted_at.isoformat() if doc.deleted_at else None,
            "company_id": doc.company_id,
            "created_by": doc.created_by,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Document details retrieval failed: {str(e)}"
        )