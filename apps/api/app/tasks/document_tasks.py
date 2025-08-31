import os
import json
import hashlib
from sqlalchemy import func
from app.services.multitenant_rag import get_multitenant_rag_service
from app.models.document import DocumentMetadata
from app.core.database import SessionLocal


async def process_document_task(
    task_id: str, file_path: str, company_id: int, uploaded_by: int
):
    """背景文檔處理任務（抽離版本）"""
    print(f"🚀 [task] 開始處理文檔: {task_id}")
    db = SessionLocal()
    document = None
    rag_service = None
    multitenant_rag = None
    try:
        document = (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.document_id == task_id)
            .first()
        )
        if not document:
            raise Exception(f"文檔記錄不存在: {task_id}")
        document.processing_status = "processing"
        db.commit()
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(company_id, db)
        result = await multitenant_rag.process_document_async(company_id, file_path, db)
        if result.get("status") != "success":
            raise Exception(result.get("message", "Unknown error"))
        lightrag_doc_id = result.get("lightrag_doc_id")
        if not lightrag_doc_id:
            raise Exception("缺少 lightrag_doc_id")
        # 嘗試讀取 LightRAG doc_status 以取得多模態與 chunk 數
        raw_status_path = os.path.join(
            "rag_storage", f"company_{company_id}", "kv_store_doc_status.json"
        )
        chunk_count = None
        multimodal = False
        raw_status_json = None
        if os.path.exists(raw_status_path):
            try:
                with open(raw_status_path, "r", encoding="utf-8") as f:
                    status_data = json.load(f)
                if lightrag_doc_id in status_data:
                    doc_status = status_data[lightrag_doc_id]
                    chunk_count = doc_status.get("chunks_count")
                    multimodal = doc_status.get("multimodal_processed", False)
                    raw_status_json = json.dumps(doc_status, ensure_ascii=False)
            except Exception as read_err:
                print(f"⚠️ 無法讀取 doc_status: {read_err}")
        # 內容雜湊（以原文件 bytes）
        file_hash = None
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
        except Exception as h_err:
            print(f"⚠️ 無法計算內容雜湊: {h_err}")
        document.processing_status = "completed"
        document.lightrag_doc_id = lightrag_doc_id
        document.processed_at = func.now()
        document.file_size = result.get("file_size", document.file_size)
        if chunk_count is not None:
            document.chunk_count = chunk_count
        document.multimodal_processed = multimodal
        if file_hash:
            document.content_hash = file_hash
        if raw_status_json:
            document.raw_status_json = raw_status_json
        db.commit()
        print(f"✅ [task] 文檔完成: {task_id}")
    except Exception as e:
        print(f"❌ [task] 文檔處理失敗 {task_id}: {e}")
        if document:
            document.processing_status = "failed"
            document.error_message = str(e)
            db.commit()
        if multitenant_rag and rag_service:
            try:
                await rag_service.delete_document(task_id, company_id)
            except Exception as cleanup_error:
                print(f"⚠️ RAG 清理失敗: {cleanup_error}")
    finally:
        try:
            db.close()
        except:
            pass
