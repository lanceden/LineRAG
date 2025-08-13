"""
RAG增強功能API端點
實現方案A的核心RAG功能：智能標籤、增強檢索、多文檔整合
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.services.smart_tagging import get_smart_tagging_service
from app.services.enhanced_search import get_enhanced_search_service
from app.services.integrated_answer import get_integrated_answer_service

router = APIRouter(prefix="/rag", tags=["RAG增強功能"])


class QueryRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10
    enable_reranking: Optional[bool] = True


class AnswerRequest(BaseModel):
    query: str
    max_sources: Optional[int] = 5
    context: Optional[List[Dict]] = []


class TaggingRequest(BaseModel):
    content: str
    filename: Optional[str] = ""


@router.post("/analyze-document")
async def analyze_document(request: TaggingRequest):
    """
    分析文檔內容，提取分類和標籤
    演示方案A的智能標籤提取功能
    """
    try:
        tagging_service = get_smart_tagging_service()
        result = await tagging_service.analyze_document(
            content=request.content,
            filename=request.filename
        )
        
        return {
            "success": True,
            "data": result,
            "message": "文檔分析完成"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文檔分析失敗: {str(e)}")


@router.post("/enhanced-search")
async def enhanced_search(request: QueryRequest):
    """
    執行增強檢索
    演示方案A的智能檢索功能
    """
    try:
        search_service = get_enhanced_search_service()
        results, analysis = await search_service.enhanced_search(
            query=request.query,
            top_k=request.max_results,
            enable_reranking=request.enable_reranking
        )
        
        # 格式化結果
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.content,
                "score": result.score,
                "metadata": result.metadata,
                "chunk_id": result.chunk_id,
                "document_id": result.document_id
            })
        
        return {
            "success": True,
            "data": {
                "results": formatted_results,
                "query_analysis": {
                    "intent": analysis.intent,
                    "entities": analysis.entities,
                    "keywords": analysis.keywords,
                    "filters": analysis.filters
                },
                "total_results": len(formatted_results)
            },
            "message": "檢索完成"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檢索失敗: {str(e)}")


@router.post("/integrated-answer")
async def integrated_answer(request: AnswerRequest):
    """
    生成多文檔整合回答
    演示方案A的核心功能：完整、準確的AI回答
    """
    try:
        answer_service = get_integrated_answer_service()
        
        if request.context:
            # 包含對話上下文的回答
            result = await answer_service.generate_conversational_answer(
                query=request.query,
                context=request.context,
                max_context=3
            )
        else:
            # 單輪問答
            result = await answer_service.generate_integrated_answer(
                query=request.query,
                max_sources=request.max_sources
            )
        
        return {
            "success": True,
            "data": {
                "answer": result.answer,
                "confidence": result.confidence,
                "answer_type": result.answer_type,
                "sources": result.sources,
                "suggestions": result.suggestions,
                "total_sources": len(result.sources)
            },
            "message": "回答生成完成"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回答生成失敗: {str(e)}")


@router.post("/multi-document-search")
async def multi_document_search(request: QueryRequest):
    """
    多文檔檢索
    從不同文檔中找到相關信息
    """
    try:
        search_service = get_enhanced_search_service()
        results = await search_service.multi_document_search(
            query=request.query,
            max_documents=request.max_results or 5
        )
        
        return {
            "success": True,
            "data": {
                "documents": results,
                "total_documents": len(results)
            },
            "message": "多文檔檢索完成"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"多文檔檢索失敗: {str(e)}")


@router.post("/upload-and-analyze")
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    上傳文件並進行智能分析
    演示完整的文檔處理流程
    """
    try:
        # 讀取文件內容
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # 進行智能分析
        tagging_service = get_smart_tagging_service()
        analysis = await tagging_service.analyze_document(
            content=text_content,
            filename=file.filename or ""
        )
        
        return {
            "success": True,
            "data": {
                "filename": file.filename,
                "file_size": len(content),
                "content_length": len(text_content),
                "analysis": analysis
            },
            "message": "文件上傳並分析完成"
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件格式不支持，請上傳文字檔案")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件處理失敗: {str(e)}")


@router.get("/demo-scenarios")
async def demo_scenarios():
    """
    提供方案A功能演示的範例場景
    """
    return {
        "success": True,
        "data": {
            "scenarios": [
                {
                    "name": "價格查詢",
                    "query": "請問產品A在台灣的保固政策和價格是什麼？",
                    "expected_features": [
                        "意圖識別：價格查詢",
                        "實體提取：產品A, 台灣",
                        "多文檔整合：產品手冊 + 價格表 + 保固政策",
                        "完整回答：包含價格和保固信息"
                    ]
                },
                {
                    "name": "故障排除",
                    "query": "產品B無法開機，該如何處理？",
                    "expected_features": [
                        "意圖識別：故障排除",
                        "文檔過濾：技術手冊, FAQ",
                        "結構化回答：排除步驟清單"
                    ]
                },
                {
                    "name": "政策說明",
                    "query": "不同地區的退換貨政策有什麼差異？",
                    "expected_features": [
                        "意圖識別：政策說明",
                        "多文檔整合：各地區政策文件",
                        "對比說明：地區間差異分析"
                    ]
                }
            ],
            "test_documents": [
                {
                    "type": "產品手冊",
                    "content": "產品A是一款高品質的電子設備，提供2年保固服務...",
                    "expected_tags": ["產品A", "保固", "電子設備", "品質"]
                },
                {
                    "type": "價格表",
                    "content": "產品A台灣地區售價：NT$5,000，包含基礎保固2年...",
                    "expected_tags": ["價格", "台灣", "NT$5000", "保固"]
                }
            ]
        },
        "message": "演示場景清單"
    }