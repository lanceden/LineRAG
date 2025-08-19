"""
知識圖譜 API 路由
提供知識圖譜查詢、統計和管理功能
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json

from app.services.multitenant_rag import get_multitenant_rag_service
from app.core.database import get_db
from app.schemas.knowledge_graph import (
    KnowledgeGraphQueryRequest,
    KnowledgeGraphStatsResponse,
    KnowledgeGraphQueryResponse,
)

# 定義 API 路由，前綴為 "/knowledge-graph"，標籤為 "knowledge-graph"
router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


@router.post("/query", response_model=KnowledgeGraphQueryResponse)
async def query_knowledge_graph(
    request: KnowledgeGraphQueryRequest, db: Session = Depends(get_db)
):
    """
    查詢知識圖譜
    根據實體名稱搜尋相關實體和關係
    """
    try:
        # 獲取多租戶 RAG 服務
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(
            request.company_id, db
        )

        # 查詢知識圖譜
        result = await rag_service.query_knowledge_graph(
            company_id=request.company_id,
            entity_name=request.entity_name,
            max_depth=request.max_depth,
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return KnowledgeGraphQueryResponse(
            status=result["status"],
            message=result["message"],
            entities=result["entities"],
            related_entities=result["related_entities"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Knowledge graph query failed: {str(e)}"
        )


@router.get("/stats/{company_id}", response_model=KnowledgeGraphStatsResponse)
async def get_knowledge_graph_stats(company_id: int, db: Session = Depends(get_db)):
    """
    取得知識圖譜統計資訊
    包括實體數量、文檔數量、關係數量等
    """
    try:
        # 獲取多租戶 RAG 服務
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(company_id, db)

        # 取得圖譜統計
        result = await rag_service.get_graph_stats(company_id)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return KnowledgeGraphStatsResponse(
            status=result["status"], company_id=company_id, stats=result["stats"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get graph stats: {str(e)}"
        )


@router.post("/create-from-document/{company_id}")
async def create_knowledge_graph_from_document(
    company_id: int, document_metadata: Dict[str, Any], db: Session = Depends(get_db)
):
    """
    從文檔建立知識圖譜
    提取實體和關係並存儲到 Neo4j
    """
    try:
        # 獲取多租戶 RAG 服務
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(company_id, db)

        # 從文檔建立知識圖譜
        result = await rag_service.create_knowledge_graph_from_document(
            file_path=document_metadata.get("file_path"),
            company_id=company_id,
            document_metadata=document_metadata,
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return {
            "status": result["status"],
            "message": result["message"],
            "document_id": result.get("document_id"),
            "entities_created": result.get("entities_created", 0),
            "relationships_created": result.get("relationships_created", 0),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create knowledge graph: {str(e)}"
        )


@router.get("/entity/{company_id}/{entity_id}")
async def get_entity_details(
    company_id: int, entity_id: str, db: Session = Depends(get_db)
):
    """
    取得實體詳細資訊
    包括實體本身和相關實體
    """
    try:
        # 獲取多租戶 RAG 服務
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(company_id, db)

        # 取得實體詳細資訊
        result = await rag_service.get_entity_details(company_id, entity_id)

        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get entity details: {str(e)}"
        )


@router.get("/entities/{company_id}/by-type/{entity_type}")
async def search_entities_by_type(
    company_id: int, entity_type: str, limit: int = 20, db: Session = Depends(get_db)
):
    """
    按類型搜尋實體
    """
    try:
        # 獲取多租戶 RAG 服務
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(company_id, db)

        # 按類型搜尋實體
        result = await rag_service.search_entities_by_type(
            company_id, entity_type, limit
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search entities: {str(e)}"
        )


@router.get("/visualization/{company_id}")
async def get_knowledge_graph_visualization(
    company_id: int,
    center_entity_id: Optional[str] = None,
    max_nodes: int = 50,
    db: Session = Depends(get_db),
):
    """
    取得知識圖譜視覺化資料
    """
    try:
        # 獲取多租戶 RAG 服務
        multitenant_rag = get_multitenant_rag_service()
        rag_service = await multitenant_rag.get_company_rag_service(company_id, db)

        # 取得視覺化資料
        result = await rag_service.get_knowledge_graph_visualization(
            company_id, center_entity_id, max_nodes
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get visualization data: {str(e)}"
        )


@router.get("/health")
async def knowledge_graph_health_check():
    """
    知識圖譜服務健康檢查
    檢查 Neo4j 連接狀態
    """
    try:
        from app.services.neo4j_service import get_neo4j_service

        neo4j_service = get_neo4j_service()

        # 檢查是否已初始化
        if not neo4j_service.initialized:
            await neo4j_service.initialize()

        # 驗證連接
        await neo4j_service.verify_connectivity()

        return {
            "status": "ok",
            "message": "Knowledge graph service is healthy",
            "neo4j_connected": True,
            "lightrag_integrated": True,
            "service": "LightRAG + Neo4j Knowledge Graph",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Knowledge graph service error: {str(e)}",
            "neo4j_connected": False,
            "lightrag_integrated": False,
            "service": "LightRAG + Neo4j Knowledge Graph",
        }
