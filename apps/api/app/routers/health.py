import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

from app.core.database import get_db
from app.services.ocr_rag_service import get_ocr_rag_service
from app.services.multitenant_rag import get_multitenant_rag_service

load_dotenv()

# 定義 API 路由，前綴為空，標籤為 "health"
router = APIRouter(prefix="", tags=["health"])


@router.get("/")
def read_root():
    """
    根目錄路由，返回 API 運行狀態。
    """
    return {"message": "LineRAG API with OCR RAG is running", "status": "ok"}


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    健康檢查路由。
    檢查 OCR RAG 服務和數據庫連接狀態。
    """
    ocr_rag_service = get_ocr_rag_service()
    multitenant_rag = get_multitenant_rag_service()

    # 測試數據庫連接
    db_status = "ok"
    try:
        # 簡單的數據庫查詢來測試連接
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 測試 Qdrant 連接
    qdrant_status = "ok"
    try:
        # 簡單測試 Qdrant 連接
        ocr_rag_service.qdrant_client.get_collections()
    except Exception as e:
        qdrant_status = f"error: {str(e)}"

    status = {
        "api": "ok",
        "ocr_rag": "ok" if ocr_rag_service.initialized else "not_initialized",
        "multitenant_rag": "ok",
        "database": db_status,
        "qdrant": qdrant_status,
        "framework": "OCR RAG + PostgreSQL + Qdrant Multi-Tenant",
        "version": "3.0.0",
    }

    # 測試 OCR RAG 服務
    if ocr_rag_service.initialized:
        try:
            # 簡單的測試查詢
            test_result = await ocr_rag_service.query("測試")
            status["test_query"] = "ok" if test_result else "no_data"
        except Exception as e:
            status["test_query"] = f"error: {str(e)}"
    else:
        status["test_query"] = "service_not_initialized"

    return status
