import os
from fastapi import APIRouter
from dotenv import load_dotenv

from app.services.vectorstore import get_vectorstore_service
from app.services.multimodal_service import get_multimodal_service
from app.services.llm import get_llm_client

load_dotenv()

# 定義 API 路由，前綴為空，標籤為 "health"
router = APIRouter(prefix="", tags=["health"])


@router.get("/")
def read_root():
    """
    根目錄路由，返回 API 運行狀態。
    """
    return {"message": "LineRAG API is running", "status": "ok"}


@router.get("/health")
def health_check():
    """
    健康檢查路由。
    檢查向量儲存、檢索器、多模態服務和 LLM 客戶端的狀態。
    如果向量儲存和檢索器可用，還會嘗試檢索測試文件以檢查數據。
    """
    vs = get_vectorstore_service()
    ms = get_multimodal_service()
    llm = get_llm_client()

    status = {
        "api": "ok",
        "vectordb": "ok" if vs.vectordb is not None else "error",
        "retriever": "ok" if vs.retriever is not None else "error",
        "mode": (
            "local"
            if os.getenv("USE_LOCAL_QDRANT", "true").lower() in {"1", "true", "yes"}
            else "server"
        ),
        "collection": os.getenv("COLLECTION_NAME", "documents"),
        "multimodal": "ok" if ms is not None else "error",
        "llm": "ok" if llm is not None else "error",
    }

    if vs.retriever is not None:
        try:
            test_docs = vs.retriever.get_relevant_documents("測試", k=1)
            status["documents_count"] = len(test_docs)
            status["has_data"] = len(test_docs) > 0
        except Exception as e:
            status["vectordb"] = "error"
            status["error"] = str(e)

    return status
