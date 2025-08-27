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
from sqlalchemy import func

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
    """原子性文檔處理任務 - 要麼全成功，要麼全失敗"""
    print(f"🚀 開始原子性文檔處理: {task_id}")

    # 創建新的資料庫 Session 用於背景任務
    from app.core.database import SessionLocal

    db = SessionLocal()
    document = None
    rag_service = None

    try:
        # 第1步：獲取文檔記錄並標記為處理中
        document = (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.document_id == task_id)
            .first()
        )

        if not document:
            raise Exception(f"文檔記錄不存在: {task_id}")

        document.processing_status = "processing"
        db.commit()
        print(f"✅ 步驟1：文檔狀態已更新為處理中")

        # 第2步：獲取 RAG 服務
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(company_id, db)
        print(f"✅ 步驟2：RAG 服務獲取成功")

        # 第3步：處理文檔並強制要求 lightrag_doc_id（避免 MinerU 阻塞）
        print(f"📄 步驟3：開始異步處理文檔 {file_path}")
        result = await multitenant_rag.process_document_async(company_id, file_path, db)
        
        # 驗證處理結果的完整性
        if result["status"] != "success":
            raise Exception(f"文檔處理失敗: {result.get('message', 'Unknown error')}")
        
        # 強制要求必須有 lightrag_doc_id
        lightrag_doc_id = result.get("lightrag_doc_id")
        if not lightrag_doc_id:
            raise Exception("文檔處理成功但缺少 lightrag_doc_id，處理不完整")
        
        print(f"✅ 步驟3：文檔處理成功，lightrag_doc_id: {lightrag_doc_id}")

        # 第4步：原子性更新資料庫
        try:
            document.processing_status = "completed"
            document.lightrag_doc_id = lightrag_doc_id
            document.processed_at = func.now()
            
            # 更新文檔統計資訊
            document.file_size = result.get("file_size", document.file_size)
            
            db.commit()
            print(f"✅ 步驟4：資料庫更新成功")
            
        except Exception as db_error:
            db.rollback()
            raise Exception(f"資料庫更新失敗: {db_error}")

        # 第5步：建立知識圖譜（可選，失敗不影響主流程）
        try:
            if hasattr(rag_service, 'create_knowledge_graph_from_document'):
                graph_result = await rag_service.create_knowledge_graph_from_document(
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
                
                if graph_result["status"] == "success":
                    document.metadata = document.metadata or {}
                    document.metadata.update({"knowledge_graph": graph_result})
                    db.commit()
                    print(f"✅ 步驟5：知識圖譜建構成功")
                
        except Exception as e:
            print(f"⚠️ 步驟5：知識圖譜建構失敗（不影響主流程）: {e}")

        print(f"🎉 文檔處理全部完成: {task_id}")

    except Exception as e:
        print(f"❌ 文檔處理失敗，開始回滾: {task_id}")
        print(f"   錯誤: {str(e)}")
        
        # 回滾操作
        try:
            # 1. 回滾資料庫狀態
            if document:
                document.processing_status = "failed"
                document.error_message = str(e)
                db.commit()
                print(f"✅ 資料庫狀態已回滾為失敗")
            
            # 2. 清理 RAG 資料（如果已處理）
            if multitenant_rag and rag_service:
                try:
                    # 使用 document_processor 的刪除方法
                    await rag_service.delete_document(task_id, str(company_id))
                    print(f"✅ RAG 資料已清理")
                except Exception as cleanup_error:
                    print(f"⚠️ RAG 資料清理失敗: {cleanup_error}")
                    
            # 3. 從資料庫中刪除文檔記錄
            if document:
                try:
                    db.delete(document)
                    db.commit()
                    print(f"✅ 文檔記錄已從資料庫刪除")
                except Exception as delete_error:
                    print(f"⚠️ 刪除文檔記錄失敗: {delete_error}")
                    db.rollback()
            
            # 4. 清理檔案系統（如果需要）
            try:
                if os.path.exists(file_path):
                    # 這裡可以選擇是否刪除原始檔案
                    # os.remove(file_path)
                    pass
            except Exception as file_cleanup_error:
                print(f"⚠️ 檔案清理警告: {file_cleanup_error}")
                
        except Exception as rollback_error:
            print(f"❌ 回滾操作失敗: {rollback_error}")
            
        # 重新拋出原始錯誤
        raise

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
    abs_file_path = file_path.absolute()  # 轉換為絕對路徑
    print(f"💾 準備保存文件到: {abs_file_path}")

    try:
        print(f"📖 開始讀取文件內容...")
        content = await file.read()
        file_size = len(content)
        print(f"📊 文件大小: {file_size} bytes ({file_size/1024/1024:.2f} MB)")

        print(f"💾 開始寫入文件...")
        with open(abs_file_path, "wb") as f:
            f.write(content)
        
        # 驗證文件寫入成功
        if not abs_file_path.exists():
            raise Exception("文件寫入後驗證失敗，文件不存在")
        
        actual_size = abs_file_path.stat().st_size
        if actual_size != file_size:
            raise Exception(f"文件大小不匹配，期望: {file_size}, 實際: {actual_size}")
            
        print(f"✅ 文件保存並驗證成功: {abs_file_path}")
        
    except Exception as e:
        print(f"❌ 文件保存失敗: {str(e)}")
        # 清理可能的部分文件
        try:
            if abs_file_path.exists():
                abs_file_path.unlink()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"文件保存失敗: {str(e)}")

    # 創建文檔記錄
    doc_id = str(uuid.uuid4())
    print(f"🆔 生成文檔ID: {doc_id}")

    document = DocumentMetadata(
        document_id=doc_id,
        original_filename=file.filename,
        file_path=str(abs_file_path),  # 使用絕對路徑
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
    print(f"   文件路徑: {abs_file_path}")
    print(f"   公司ID: {company_id}")
    print(f"   用戶ID: {current_user.id}")

    background_tasks.add_task(
        process_document_task,
        doc_id,
        str(abs_file_path),  # 使用絕對路徑
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
