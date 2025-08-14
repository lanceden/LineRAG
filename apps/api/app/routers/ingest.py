"""
文檔擷取處理 API 路由
使用 RAG-Anything 處理多模態文檔，支援多租戶架構
"""

import os
import uuid
import json
from typing import Dict, Any, List
from pathlib import Path

from fastapi import (
    APIRouter,
    HTTPException,
    BackgroundTasks,
    UploadFile,
    File,
    Form,
    Depends,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.multitenant_rag import get_multitenant_rag_service
from app.services.multitenant_user import get_multitenant_user_service
from app.models.document import DocumentMetadata
from app.schemas.ingest import IngestRequest, IngestResponse

router = APIRouter(prefix="", tags=["ingest"])


async def process_document_task(
    task_id: str, file_path: str, company_id: int, user_id: int, db: Session
):
    """背景任務：處理文檔"""
    try:
        # 更新文檔狀態為處理中
        document = (
            db.query(DocumentMetadata).filter(DocumentMetadata.id == task_id).first()
        )

        if document:
            document.status = "processing"
            db.commit()

        # 獲取多租戶 RAG 服務
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(company_id, db)

        # 使用 RAG-Anything 處理文檔
        result = await rag_service.process_document(file_path, str(company_id))

        if result["status"] == "success":
            # 更新文檔狀態為完成
            if document:
                document.status = "completed"
                document.metadata = result
                db.commit()
        else:
            # 更新文檔狀態為失敗
            if document:
                document.status = "failed"
                document.error_message = result["message"]
                db.commit()

    except Exception as e:
        # 更新文檔狀態為失敗
        document = (
            db.query(DocumentMetadata).filter(DocumentMetadata.id == task_id).first()
        )
        if document:
            document.status = "failed"
            document.error_message = str(e)
            db.commit()


@router.post("/ingest/document", response_model=IngestResponse)
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company_id: int = Form(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """
    上傳並處理單個文檔
    支援 PDF、Office 文檔、圖像等格式
    """
    # 檢查用戶權限
    user_service = get_multitenant_user_service()
    user = await user_service.get_user_by_id(user_id, db)
    if not user or user.company_id != company_id:
        raise HTTPException(status_code=403, detail="沒有權限訪問此公司資源")

    # 檢查文件格式
    allowed_extensions = {
        ".pdf",
        ".docx",
        ".pptx",
        ".xlsx",
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
    }
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支援的文件格式: {file_extension}. 支援的格式: {', '.join(allowed_extensions)}",
        )

    # 創建上傳目錄
    upload_dir = Path("uploads") / str(company_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 保存上傳的文件
    file_path = upload_dir / file.filename

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失敗: {str(e)}")

    # 創建文檔記錄
    document_id = str(uuid.uuid4())
    document = DocumentMetadata(
        id=document_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        file_type=file_extension,
        company_id=company_id,
        uploaded_by=user_id,
        status="queued",
    )

    try:
        db.add(document)
        db.commit()
        db.refresh(document)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"資料庫錯誤: {str(e)}")

    # 啟動背景任務
    background_tasks.add_task(
        process_document_task, document_id, str(file_path), company_id, user_id, db
    )

    return IngestResponse(
        task_id=document_id,
        status="queued",
        message=f"文檔 {file.filename} 已加入處理佇列",
    )


@router.post("/ingest/folder")
async def ingest_folder(
    background_tasks: BackgroundTasks,
    folder_path: str = Form(...),
    company_id: int = Form(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """
    批量處理資料夾中的文檔
    """
    # 檢查用戶權限
    user_service = get_multitenant_user_service()
    user = await user_service.get_user_by_id(user_id, db)
    if not user or user.company_id != company_id:
        raise HTTPException(status_code=403, detail="沒有權限訪問此公司資源")

    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        raise HTTPException(status_code=400, detail="資料夾路徑不存在")

    # 創建批次任務 ID
    batch_id = str(uuid.uuid4())

    async def process_folder_task():
        try:
            # 獲取多租戶 RAG 服務
            multitenant_rag = get_multitenant_rag_service()
            rag_service = await multitenant_rag.get_company_rag_service(company_id, db)

            # 使用 RAG-Anything 批量處理
            result = await rag_service.process_folder(folder_path, str(company_id))

            # 為批次中的每個文件創建文檔記錄
            if result["status"] == "success" and "processed_files" in result:
                for file_info in result["processed_files"]:
                    document = DocumentMetadata(
                        id=str(uuid.uuid4()),
                        filename=file_info["filename"],
                        file_path=file_info["path"],
                        file_size=file_info.get("size", 0),
                        file_type=Path(file_info["filename"]).suffix.lower(),
                        company_id=company_id,
                        uploaded_by=user_id,
                        status="completed",
                        metadata=file_info,
                    )
                    db.add(document)

                db.commit()

        except Exception as e:
            # 記錄錯誤
            print(f"批次處理失敗: {str(e)}")

    # 啟動背景任務
    background_tasks.add_task(process_folder_task)

    return IngestResponse(
        task_id=batch_id,
        status="queued",
        message=f"資料夾 {folder_path} 已加入處理佇列",
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
    user_service = get_multitenant_user_service()
    user = await user_service.get_user_by_id(request.user_id, db)
    if not user or user.company_id != request.company_id:
        raise HTTPException(status_code=403, detail="沒有權限訪問此公司資源")

    task_id = str(uuid.uuid4())

    async def process_content_task():
        try:
            # 獲取多租戶 RAG 服務
            multitenant_rag = get_multitenant_rag_service()
            rag_service = await multitenant_rag.get_company_rag_service(
                request.company_id, db
            )

            # 插入內容列表
            result = await rag_service.insert_content_list(
                content_list=request.content_list,
                file_path=request.file_path,
                company_id=str(request.company_id),
            )

            if result["status"] == "success":
                # 創建文檔記錄
                document = DocumentMetadata(
                    id=task_id,
                    filename=(
                        Path(request.file_path).name
                        if request.file_path
                        else "直接內容"
                    ),
                    file_path=request.file_path or "",
                    file_size=len(str(request.content_list)),
                    file_type="content",
                    company_id=request.company_id,
                    uploaded_by=request.user_id,
                    status="completed",
                    metadata=result,
                )
                db.add(document)
                db.commit()

        except Exception as e:
            # 創建失敗記錄
            document = DocumentMetadata(
                id=task_id,
                filename=(
                    Path(request.file_path).name if request.file_path else "直接內容"
                ),
                file_path=request.file_path or "",
                file_size=len(str(request.content_list)),
                file_type="content",
                company_id=request.company_id,
                uploaded_by=request.user_id,
                status="failed",
                error_message=str(e),
            )
            db.add(document)
            db.commit()

    # 啟動背景任務
    background_tasks.add_task(process_content_task)

    return IngestResponse(
        task_id=task_id, status="queued", message="內容列表已加入處理佇列"
    )


@router.get("/ingest/status/{task_id}")
async def get_ingest_status(task_id: str, db: Session = Depends(get_db)):
    """
    檢查擷取任務狀態
    """
    document = db.query(DocumentMetadata).filter(DocumentMetadata.id == task_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="任務不存在")

    return {
        "task_id": task_id,
        "status": document.status,
        "filename": document.filename,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "file_type": document.file_type,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "metadata": document.metadata,
        "error_message": document.error_message,
    }


@router.get("/ingest/documents/{company_id}")
async def list_company_documents(
    company_id: int,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    列出公司的所有文檔
    """
    # 檢查用戶權限
    user_service = get_multitenant_user_service()
    user = await user_service.get_user_by_id(user_id, db)
    if not user or user.company_id != company_id:
        raise HTTPException(status_code=403, detail="沒有權限訪問此公司資源")

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
                "filename": doc.filename,
                "file_path": doc.file_path,
                "file_size": doc.file_size,
                "file_type": doc.file_type,
                "status": doc.status,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at,
                "error_message": doc.error_message,
            }
            for doc in documents
        ],
        "total": len(documents),
        "skip": skip,
        "limit": limit,
    }


@router.delete("/ingest/document/{document_id}")
async def delete_document(
    document_id: str,
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    刪除文檔及其相關數據
    """
    # 獲取文檔
    document = (
        db.query(DocumentMetadata).filter(DocumentMetadata.id == document_id).first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="文檔不存在")

    # 檢查用戶權限
    user_service = get_multitenant_user_service()
    user = await user_service.get_user_by_id(user_id, db)
    if not user or user.company_id != document.company_id:
        raise HTTPException(status_code=403, detail="沒有權限訪問此公司資源")

    # 從 RAG 服務中刪除文檔數據
    try:
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(
            document.company_id, db
        )
        await rag_service.delete_document(document.file_path)
    except Exception as e:
        print(f"從 RAG 服務刪除文檔時出錯: {str(e)}")

    # 刪除文件系統中的文件
    try:
        if document.file_path and Path(document.file_path).exists():
            Path(document.file_path).unlink()
    except Exception as e:
        print(f"刪除文件時出錯: {str(e)}")

    # 從資料庫中刪除記錄
    db.delete(document)
    db.commit()

    return {"message": f"文檔 {document.filename} 已成功刪除"}
