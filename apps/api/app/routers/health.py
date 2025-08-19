import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

from app.core.database import get_db
from app.services.rag_anything import get_rag_service
from app.services.multitenant_rag import get_multitenant_rag_service
from app.services.neo4j_service import get_neo4j_service

load_dotenv()

# 定義 API 路由，前綴為空，標籤為 "health"
router = APIRouter(prefix="", tags=["health"])


@router.get("/")
def read_root():
    """
    根目錄路由，返回 API 運行狀態。
    """
    return {"message": "LineRAG API with RAG-Anything is running", "status": "ok"}


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    健康檢查路由。
    檢查 RAG-Anything 服務和數據庫連接狀態。
    """
    rag_service = get_rag_service()
    multitenant_rag = get_multitenant_rag_service()

    # 測試數據庫連接
    db_status = "ok"
    try:
        # 簡單的數據庫查詢來測試連接
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 測試 Neo4j 連接
    neo4j_status = "ok"
    try:
        neo4j_service = get_neo4j_service()
        if not neo4j_service.initialized:
            await neo4j_service.initialize()
        await neo4j_service.verify_connectivity()
    except Exception as e:
        neo4j_status = f"error: {str(e)}"

    status = {
        "api": "ok",
        "rag_anything": rag_service.get_status(),
        "multitenant_rag": "ok",
        "database": db_status,
        "neo4j": neo4j_status,
        "framework": "RAG-Anything + PostgreSQL + Neo4j Multi-Tenant",
        "version": "2.0.0",
    }

    # 測試 RAG-Anything 服務
    if rag_service.initialized:
        try:
            # 簡單的測試查詢
            test_result = await rag_service.query_text("測試", mode="naive")
            status["test_query"] = "ok" if test_result else "no_data"
        except Exception as e:
            status["test_query"] = f"error: {str(e)}"
    else:
        status["test_query"] = "service_not_initialized"

    return status
