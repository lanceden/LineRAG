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
    Request,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_user
from app.services.multitenant_rag import get_multitenant_rag_service
from app.services.multitenant_user import get_multitenant_user_service
from app.models.document import DocumentMetadata
from app.models.system_user import SystemUser
from app.schemas.ingest import IngestRequest, IngestResponse

router = APIRouter(prefix="", tags=["ingest"])


async def process_document_task(
    task_id: str, file_path: str, company_id: int, uploaded_by: int
):
    """背景任務：處理文檔"""
    print(f"🚀 開始處理文檔背景任務: {task_id}")

    # 創建新的資料庫 Session 用於背景任務
    from app.core.database import SessionLocal

    db = SessionLocal()

    try:
        # 更新文檔狀態為處理中
        document = (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.document_id == task_id)
            .first()
        )

        if document:
            document.processing_status = "processing"
            db.commit()
            print(f"📝 文檔狀態已更新為處理中: {task_id}")

        # 獲取多租戶 RAG 服務
        print(f"🔧 獲取 RAG 服務...")
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(company_id, db)
        print(f"✅ RAG 服務獲取成功")

        # 使用 RAG-Anything 處理文檔
        print(f"📄 開始處理文檔: {file_path}")
        result = await rag_service.process_document(file_path, str(company_id))
        print(f"📄 文檔處理結果: {result.get('status', 'unknown')}")

        if result["status"] == "success":
            # 更新文檔狀態為完成
            if document:
                document.processing_status = "completed"
                
                # 計算並存儲 LightRAG doc_id (企業級做法)
                # 注意：需要從 RAG 處理結果中獲取實際的 doc_id
                try:
                    # 方法1：從處理結果中獲取 doc_id
                    if "lightrag_doc_id" in result:
                        lightrag_doc_id = result["lightrag_doc_id"]
                        document.lightrag_doc_id = lightrag_doc_id
                        print(f"💾 從處理結果獲取並存儲 LightRAG doc_id: {lightrag_doc_id}")
                    else:
                        print(f"⚠️  處理結果中沒有 lightrag_doc_id，嘗試其他方法...")
                        # 方法2：從 LightRAG 實例中查詢最新的 doc_id
                        lightrag_doc_id = await rag_service.get_latest_doc_id()
                        if lightrag_doc_id:
                            document.lightrag_doc_id = lightrag_doc_id
                            print(f"💾 從 RAG 實例獲取並存儲 LightRAG doc_id: {lightrag_doc_id}")
                        else:
                            print(f"⚠️  無法獲取 LightRAG doc_id")
                
                except Exception as e:
                    print(f"⚠️  計算 LightRAG doc_id 失敗: {e}")
                    # 不影響主流程
                
                db.commit()

                # 建立知識圖譜
                try:
                    graph_result = (
                        await rag_service.create_knowledge_graph_from_document(
                            file_path=file_path,
                            company_id=company_id,
                            document_metadata={
                                "id": document.id,
                                "filename": document.original_filename,
                                "file_path": file_path,
                                "file_type": document.mime_type,
                                "file_size": document.file_size,
                            },
                        )
                    )

                    # 更新文檔元資料包含圖譜資訊
                    if graph_result["status"] == "success":
                        document.metadata.update({"knowledge_graph": graph_result})
                        db.commit()

                except Exception as e:
                    # 圖譜建構失敗不影響文檔處理
                    print(f"Knowledge graph creation failed: {e}")
        else:
            # 更新文檔狀態為失敗
            if document:
                document.processing_status = "failed"
                document.error_message = result["message"]
                db.commit()

    except Exception as e:
        print(f"❌ 背景任務處理失敗: {task_id}, 錯誤: {str(e)}")
        import traceback

        print(f"📋 錯誤詳情: {traceback.format_exc()}")

        # 更新文檔狀態為失敗
        try:
            document = (
                db.query(DocumentMetadata)
                .filter(DocumentMetadata.document_id == task_id)
                .first()
            )
            if document:
                document.processing_status = "failed"
                document.error_message = str(e)
                db.commit()
                print(f"📝 文檔狀態已更新為失敗: {task_id}")
        except Exception as db_error:
            print(f"❌ 更新文檔狀態失敗: {str(db_error)}")
    finally:
        # 確保資料庫連接被關閉
        try:
            db.close()
            print(f"🔒 資料庫連接已關閉: {task_id}")
        except Exception as close_error:
            print(f"❌ 關閉資料庫連接失敗: {str(close_error)}")


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

    # TODO: 待實現權限檢查邏輯

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
    print(f"🔍 檢查文件格式: {file_extension}")

    if file_extension not in allowed_extensions:
        print(f"❌ 不支援的文件格式: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail=f"不支援的文件格式: {file_extension}. 支援的格式: {', '.join(allowed_extensions)}",
        )

    print(f"✅ 文件格式檢查通過: {file_extension}")

    # 創建上傳目錄
    upload_dir = Path("uploads") / f"company_{company_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 創建上傳目錄: {upload_dir}")

    # 保存上傳的文件
    file_path = upload_dir / file.filename
    print(f"💾 準備保存文件到: {file_path}")

    try:
        print(f"📖 開始讀取文件內容...")
        content = await file.read()
        file_size = len(content)
        print(f"📊 文件大小: {file_size} bytes ({file_size/1024/1024:.2f} MB)")

        print(f"💾 開始寫入文件...")
        with open(file_path, "wb") as f:
            f.write(content)
        print(f"✅ 文件保存成功: {file_path}")
    except Exception as e:
        print(f"❌ 文件保存失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件保存失敗: {str(e)}")

    # 創建文檔記錄
    doc_id = str(uuid.uuid4())
    print(f"🆔 生成文檔ID: {doc_id}")

    document = DocumentMetadata(
        document_id=doc_id,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file_extension,
        company_id=company_id,
        created_by=current_user.username or str(current_user.id),
        processing_status="pending",
    )
    print(f"📝 創建文檔記錄: {file.filename} -> 狀態: pending")

    try:
        print(f"💾 保存文檔記錄到資料庫...")
        db.add(document)
        db.commit()
        db.refresh(document)
        print(f"✅ 文檔記錄保存成功，資料庫ID: {document.id}")
    except Exception as e:
        print(f"❌ 資料庫錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"資料庫錯誤: {str(e)}")

    # 啟動背景任務
    print(f"🚀 啟動背景處理任務...")
    print(f"   任務ID: {doc_id}")
    print(f"   文件路徑: {file_path}")
    print(f"   公司ID: {company_id}")
    print(f"   用戶ID: {current_user.id}")

    background_tasks.add_task(
        process_document_task,
        doc_id,
        str(file_path),
        company_id,
        current_user.id,
    )
    print(f"✅ 背景任務已加入佇列")
    print("=" * 80)

    return IngestResponse(
        task_id=doc_id,
        status="pending",
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
                        document_id=str(uuid.uuid4()),
                        original_filename=file_info["filename"],
                        file_path=file_info["path"],
                        file_size=file_info.get("size", 0),
                        mime_type=Path(file_info["filename"]).suffix.lower(),
                        company_id=company_id,
                        created_by=str(user_id),
                        processing_status="completed",
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
    user_service = get_multitenant_user_service(db)
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
                    document_id=task_id,
                    original_filename=(
                        Path(request.file_path).name
                        if request.file_path
                        else "直接內容"
                    ),
                    file_path=request.file_path or "",
                    file_size=len(str(request.content_list)),
                    mime_type="content",
                    company_id=request.company_id,
                    created_by=str(request.user_id),
                    processing_status="completed",
                )
                db.add(document)
                db.commit()

        except Exception as e:
            # 創建失敗記錄
            document = DocumentMetadata(
                document_id=task_id,
                original_filename=(
                    Path(request.file_path).name if request.file_path else "直接內容"
                ),
                file_path=request.file_path or "",
                file_size=len(str(request.content_list)),
                mime_type="content",
                company_id=request.company_id,
                created_by=str(request.user_id),
                processing_status="failed",
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
                "created_at": doc.uploaded_at,
                "processed_at": doc.processed_at,
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

    # 從 RAG 服務中刪除文檔數據
    try:
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(
            document.company_id, db
        )
        # 使用 document_id 和 company_id 作為參數
        await rag_service.delete_document(
            document.document_id, str(document.company_id)
        )
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

    return {"message": f"文檔 {document.original_filename} 已成功刪除"}
