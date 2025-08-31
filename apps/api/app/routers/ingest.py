"""文檔擷取處理 API 路由"""

import os
import uuid
from pathlib import Path
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
from app.services.ingestion_service import get_ingestion_service
from app.utils.file_storage import (
    validate_extension,
    generate_doc_id_and_unique_name,
    write_file_bytes,
)
from app.utils.audit_helper import create_audit
from app.tasks.document_tasks import (
    process_document_task as background_process_document_task,
)
from app.tasks.folder_tasks import process_folder_task as background_process_folder_task
from app.tasks.content_tasks import (
    process_content_task as background_process_content_task,
)
from app.services.multitenant_user import get_multitenant_user_service
from app.services.multitenant_rag import get_multitenant_rag_service
from neo4j import GraphDatabase as _Neo4jDriver

router = APIRouter(prefix="", tags=["ingest"])


@router.post("/ingest/document", response_model=IngestResponse)
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """
    上傳並處理單個文檔
    支援 PDF、Office 文檔、圖像等格式
    """
    print("=" * 80)
    print(f"📤 開始文檔上傳流程")
    print(f"   文件名: {file.filename}")
    print(f"   公司ID: {company_id}")
    print(f"   用戶: {current_user.username} (ID: {current_user.id})")
    print(f"   Content-Type: {file.content_type}")
    print("=" * 80)

    # TODO: 權限檢查（後續補）

    # 驗證副檔名 / 產生唯一檔名
    try:
        ext = validate_extension(file.filename)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    doc_id, unique_filename = generate_doc_id_and_unique_name(file.filename)
    print(f"🆔 文檔ID: {doc_id} (stored name: {unique_filename})")

    # 創建上傳目錄
    upload_dir = Path("uploads") / f"company_{company_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 創建上傳目錄: {upload_dir}")

    try:
        print(f"📖 讀取文件內容...")
        content = await file.read()
        file_size = len(content)
        abs_file_path = write_file_bytes(upload_dir, unique_filename, content)
        print(f"✅ 文件保存成功: {abs_file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失敗: {e}")

    # 創建文檔記錄（使用預先產生的 doc_id 與真實 MIME）
    ingestion_service = get_ingestion_service(db)
    try:
        document = ingestion_service.create_pending_document(
            document_id=doc_id,
            original_filename=file.filename,
            stored_path=str(abs_file_path),
            size=file_size,
            mime=file.content_type or ext,
            company_id=company_id,
            created_by=current_user.username or str(current_user.id),
        )
        create_audit(
            db,
            company_id=company_id,
            action="document_upload",
            resource_type="document",
            resource_id=document.document_id,
            endpoint="/ingest/document",
            method="POST",
            status="success",
            system_user_id=current_user.id,
            request_data={
                "filename": document.original_filename,
                "size": document.file_size,
                "mime": document.mime_type,
            },
        )
        print(f"✅ 文檔記錄建立 (DB id={document.id})")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"資料庫錯誤: {e}")

    # 啟動背景任務
    print(f"🚀 啟動背景處理任務...")
    print(f"   任務ID: {doc_id}")
    print(f"   文件路徑: {abs_file_path}")
    print(f"   公司ID: {company_id}")
    print(f"   用戶ID: {current_user.id}")

    # 啟動背景任務（文件處理）
    background_tasks.add_task(
        background_process_document_task,
        doc_id,
        str(abs_file_path),
        company_id,
        current_user.id,
    )
    return IngestResponse(
        task_id=doc_id,
        status="pending",
        message=f"文檔 {file.filename} 已加入處理佇列",
    )


@router.post("/ingest/content")
async def ingest_content_list(
    background_tasks: BackgroundTasks,
    request: IngestRequest,
    db: Session = Depends(get_db),
):
    """
    直接插入內容列表
    支援預解析的多模態內容
    """
    # 檢查用戶權限
    user_service = get_multitenant_user_service(db)
    user = await user_service.get_user_by_id(request.user_id, db)
    if not user or user.company_id != request.company_id:
        raise HTTPException(status_code=403, detail="沒有權限訪問此公司資源")

    task_id = str(uuid.uuid4())

    # 啟動背景任務（改為外部 task）
    background_tasks.add_task(
        background_process_content_task,
        task_id,
        request.company_id,
        request.user_id,
        request.content_list,
        request.file_path,
    )

    return IngestResponse(
        task_id=task_id, status="queued", message="內容列表已加入處理佇列"
    )


@router.get("/ingest/status/{task_id}")
async def get_ingest_status(task_id: str, db: Session = Depends(get_db)):
    """
    檢查擷取任務狀態
    """
    document = (
        db.query(DocumentMetadata)
        .filter(DocumentMetadata.document_id == task_id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="任務不存在")

    return {
        "task_id": task_id,
        "status": document.processing_status,
        "filename": document.original_filename,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "file_type": document.mime_type,
        "created_at": document.uploaded_at,
        "processed_at": document.processed_at,
        "error_message": document.error_message,
        "multimodal_processed": document.multimodal_processed,
        "chunk_count": document.chunk_count,
        "lightrag_doc_id": document.lightrag_doc_id,
    }


@router.get("/ingest/documents/{company_id}")
async def list_company_documents(
    company_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """
    列出公司的所有文檔
    """
    # TODO: 待實現權限檢查邏輯

    documents = (
        db.query(DocumentMetadata)
        .filter(DocumentMetadata.company_id == company_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "documents": [
            {
                "id": doc.id,
                "document_id": doc.document_id,
                "filename": doc.original_filename,
                "file_path": doc.file_path,
                "file_size": doc.file_size,
                "file_type": doc.mime_type,
                "status": doc.processing_status,
                "multimodal_processed": doc.multimodal_processed,
                "chunk_count": doc.chunk_count,
                "created_at": doc.uploaded_at,
                "processed_at": doc.processed_at,
                "error_message": doc.error_message,
            }
            for doc in documents
        ],
        "total": db.query(DocumentMetadata)
        .filter(DocumentMetadata.company_id == company_id)
        .count(),
        "skip": skip,
        "limit": limit,
    }


@router.delete("/ingest/document/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """
    刪除文檔及其相關數據
    """
    # 獲取文檔 - 支援 id 或 document_id 查詢
    document = None

    # 先嘗試用數字 id 查詢
    if document_id.isdigit():
        document = (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.id == int(document_id))
            .first()
        )

    # 如果沒找到，再用 document_id (UUID) 查詢
    if not document:
        document = (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.document_id == document_id)
            .first()
        )

    if not document:
        raise HTTPException(status_code=404, detail="文檔不存在")

    # 若仍在處理中，禁止刪除（避免一致性問題）
    if document.processing_status in ("pending", "processing"):
        # 審計：刪除被阻擋
        create_audit(
            db,
            company_id=document.company_id,
            system_user_id=current_user.id,
            action="document_delete_blocked",
            resource_type="document",
            resource_id=document.document_id,
            endpoint=f"/ingest/document/{document_id}",
            method="DELETE",
            status="failed",
            error_message=f"Cannot delete while status={document.processing_status}",
        )
        raise HTTPException(
            status_code=409,
            detail=f"文檔目前狀態為 {document.processing_status}，不可刪除",
        )

    # 從 RAG 服務中刪除文檔數據
    try:
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(
            document.company_id, db
        )
        # 使用 document_id 和 company_id 作為參數
        await rag_service.delete_document(document.document_id, document.company_id)
    except Exception as e:
        print(f"從 RAG 服務刪除文檔時出錯: {str(e)}")

    # 刪除文件系統中的文件
    try:
        if document.file_path and Path(document.file_path).exists():
            Path(document.file_path).unlink()
    except Exception as e:
        print(f"刪除文件時出錯: {str(e)}")

    # 從資料庫中刪除記錄 (仍為硬刪；後續可改軟刪)
    original_filename = document.original_filename
    resource_id = document.document_id
    company_id_val = document.company_id
    db.delete(document)
    db.commit()

    # 審計：刪除
    create_audit(
        db,
        company_id=company_id_val,
        system_user_id=current_user.id,
        action="document_delete",
        resource_type="document",
        resource_id=resource_id,
        endpoint=f"/ingest/document/{document_id}",
        method="DELETE",
        status="success",
    )

    return {"message": f"文檔 {original_filename} 已成功刪除"}


@router.get("/ingest/document/detail/{document_id}")
async def get_document_detail(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """取得單一文檔詳細狀態（含多模態與原始狀態 JSON）"""
    query = db.query(DocumentMetadata)
    doc = None
    if document_id.isdigit():
        doc = query.filter(DocumentMetadata.id == int(document_id)).first()
    if not doc:
        doc = query.filter(DocumentMetadata.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文檔不存在")
    return {
        "document_id": doc.document_id,
        "filename": doc.original_filename,
        "status": doc.processing_status,
        "multimodal_processed": doc.multimodal_processed,
        "chunk_count": doc.chunk_count,
        "lightrag_doc_id": doc.lightrag_doc_id,
        "content_hash": doc.content_hash,
        "file_size": doc.file_size,
        "mime_type": doc.mime_type,
        "uploaded_at": doc.uploaded_at,
        "processed_at": doc.processed_at,
        "error_message": doc.error_message,
        "raw_status": doc.raw_status_json,
    }


@router.get("/debug/neo4j/stats")
async def neo4j_stats(
    current_user: SystemUser = Depends(get_current_user),
    uri: str = None,
    user: str = None,
    password: str = None,
):
    """(TEST ONLY) Neo4j 節點/關係統計；僅限管理員。部署時將移除。"""
    # 簡易權限：僅 username = 'admin' 或 is_active=True 帳號；可再細化
    if not current_user or current_user.username != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    neo4j_uri = uri or os.getenv("NEO4J_URL", "bolt://localhost:7687")
    neo4j_user = user or os.getenv("NEO4J_USER", "neo4j")
    neo4j_pwd = password or os.getenv("NEO4J_PASSWORD", "password")
    try:
        driver = _Neo4jDriver.driver(neo4j_uri, auth=(neo4j_user, neo4j_pwd))
        with driver.session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        driver.close()
        return {
            "nodes": nodes,
            "relationships": rels,
            "uri": neo4j_uri,
            "test_endpoint": True,
        }
    except Exception as e:
        return {"error": str(e), "uri": neo4j_uri, "test_endpoint": True}
