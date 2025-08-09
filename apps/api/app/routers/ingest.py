import os
import time
import uuid
import json
from typing import Dict, Any, List, Tuple

from fastapi import APIRouter, HTTPException, BackgroundTasks
import redis.asyncio as redis

# Load .env
from app.core import env
from app.services.vectorstore import get_vectorstore_service
from langchain.schema import Document
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    Docx2txtLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.schemas.ingest import IngestRequest

router = APIRouter(prefix="", tags=["ingest"])


# Redis connection
def get_redis_client():
    """獲取 Redis 客戶端"""
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True,
    )


async def set_task_status(task_id: str, status: Dict[str, Any]):
    """設定任務狀態到 Redis"""
    redis_client = get_redis_client()
    try:
        await redis_client.setex(
            f"task:{task_id}", 3600, json.dumps(status)  # 1小時過期
        )
    finally:
        await redis_client.close()


async def get_task_status(task_id: str) -> Dict[str, Any]:
    """從 Redis 獲取任務狀態"""
    redis_client = get_redis_client()
    try:
        result = await redis_client.get(f"task:{task_id}")
        if result:
            return json.loads(result)
        return {"status": "not_found"}
    finally:
        await redis_client.close()


def add_document_to_vectorstore(
    file_path: str, original_name: str, use_ocr: bool = False
) -> str:
    """
    將文件添加到向量儲存中。
    根據 use_ocr 參數決定是否使用 OCR 進行文字提取。
    如果文件是 PDF 或 Word 文件，則載入並分割成塊，然後添加到向量儲存。
    為每個塊添加元數據，包括文件 ID、檔名、上傳時間和處理方法。
    """
    vs = get_vectorstore_service()
    if vs.vectordb is None:
        raise HTTPException(status_code=500, detail="向量庫未初始化")

    # 生成文件 ID
    doc_id = str(uuid.uuid4())
    documents: List[Document] = []

    if use_ocr:
        # OCR 模式：交給現有 document_processor（維持行為一致）
        try:
            from app.services.document_processor import get_document_processor

            dp = get_document_processor()
            extracted_texts = dp.process_document_with_ocr(file_path, original_name)
            for page_num, text in extracted_texts:
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "page_number": page_num,
                            "source": original_name,
                            "extraction_method": "ocr",
                        },
                    )
                )
        except Exception as ocr_error:
            # OCR 失敗，降級為傳統文字提取
            print(f"OCR failed, falling back to traditional extraction: {ocr_error}")
            use_ocr = False

    if not use_ocr:
        # 傳統文字抽取
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == ".pdf":
            loader = PyMuPDFLoader(file_path)
        elif file_extension in [".doc", ".docx"]:
            try:
                loader = Docx2txtLoader(file_path)
            except Exception:
                try:
                    loader = UnstructuredWordDocumentLoader(file_path)
                except Exception as e2:
                    raise HTTPException(
                        status_code=400, detail=f"無法載入 Word 文件: {str(e2)}"
                    )
        else:
            raise HTTPException(status_code=400, detail="不支援的文件格式")
        documents = loader.load()

    if not documents:
        raise HTTPException(status_code=400, detail="無法從文件中提取內容")

    # 分塊前記錄共用欄位
    upload_time = time.time()

    # 分塊
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)

    total_chunks = len(chunks)
    for chunk in chunks:
        # 標註文件層級 metadata，供 Qdrant 直接查詢
        chunk.metadata["doc_id"] = doc_id
        chunk.metadata["filename"] = original_name
        chunk.metadata["upload_time"] = upload_time
        chunk.metadata["chunk_count"] = total_chunks
        chunk.metadata["processing_method"] = "ocr" if use_ocr else "traditional"

    # 寫入向量庫
    vs.vectordb.add_documents(chunks)

    return doc_id


@router.post("/ingest")
def ingest_document(request: IngestRequest):
    """
    同步處理文件並將其添加到向量儲存。
    接收 IngestRequest 物件，其中包含文件路徑、原始檔名和是否使用 OCR 的選項。
    """
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    allowed_extensions = [".pdf", ".doc", ".docx"]
    file_extension = os.path.splitext(request.file_path)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="不支援的文件格式")

    doc_id = add_document_to_vectorstore(
        request.file_path, request.original_name, request.use_ocr
    )
    return {
        "message": "文件處理成功",
        "doc_id": doc_id,
        "filename": request.original_name,
        "status": "success",
    }


@router.post("/ingest-async")
async def ingest_document_async(request: IngestRequest, background: BackgroundTasks):
    """
    異步處理文件並將其添加到向量儲存。
    返回一個任務 ID，用於追蹤處理狀態。
    """
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    task_id = uuid.uuid4().hex
    await set_task_status(task_id, {"status": "pending"})

    async def _run():
        await set_task_status(task_id, {"status": "processing"})
        try:
            doc_id = add_document_to_vectorstore(
                request.file_path, request.original_name, request.use_ocr
            )
            await set_task_status(
                task_id,
                {"status": "done", "doc_id": doc_id, "filename": request.original_name},
            )
        except Exception as e:
            await set_task_status(task_id, {"status": "error", "error": str(e)})

    background.add_task(_run)
    return {"task_id": task_id, "status": "queued"}


@router.get("/tasks/{task_id}")
async def get_task_status_route(task_id: str):
    """獲取任務狀態"""
    return await get_task_status(task_id)


from typing import Generator


def _iter_points(limit: int = 256) -> Generator[List[Any], None, None]:
    """
    迭代獲取向量儲存中的點（數據塊）。
    用於分批讀取數據，避免一次性載入過多數據。
    """
    vs = get_vectorstore_service()
    client = vs.qdrant_client
    collection = vs.vectordb.collection_name
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=limit,
            with_payload=True,
            with_vectors=False,
            offset=offset,
        )
        if not points:
            break
        yield points
        if offset is None:
            break


@router.get("/documents")
def list_documents():
    """
    列出所有已處理的文件。
    從向量儲存中讀取文件元數據，並返回文件列表，包含文件 ID、檔名、上傳日期和塊數。
    """
    vs = get_vectorstore_service()
    if vs.vectordb is None or vs.qdrant_client is None:
        raise HTTPException(status_code=500, detail="向量庫未初始化")

    docs: Dict[str, Dict[str, Any]] = {}
    for batch in _iter_points():
        for p in batch:
            meta = (p.payload or {}).get("metadata", {})
            doc_id = meta.get("doc_id")
            if not doc_id:
                continue
            if doc_id not in docs:
                docs[doc_id] = {
                    "doc_id": doc_id,
                    "filename": meta.get("filename"),
                    "upload_time": meta.get("upload_time"),
                    "chunk_count": meta.get("chunk_count"),
                }

    documents = []
    for d in docs.values():
        upload_date = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(d.get("upload_time", time.time()))
        )
        documents.append(
            {
                "doc_id": d["doc_id"],
                "filename": d.get("filename"),
                "upload_date": upload_date,
                "chunk_count": d.get("chunk_count", 0),
            }
        )

    return {"documents": documents, "total_count": len(documents)}


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """
    根據文件 ID 刪除向量儲存中的文件。
    """
    vs = get_vectorstore_service()
    if vs.vectordb is None or vs.qdrant_client is None:
        raise HTTPException(status_code=500, detail="向量庫未初始化")

    vs.qdrant_client.delete(
        collection_name=vs.vectordb.collection_name,
        points_selector=Filter(
            must=[FieldCondition(key="metadata.doc_id", match=MatchValue(value=doc_id))]
        ),
    )

    return {"message": "刪除請求已送出", "doc_id": doc_id}
