from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
from typing import Optional

from app.schemas.ask import AskRequest, MultimodalAskRequest
from app.services.multitenant_rag import get_multitenant_rag_service
from app.core.database import get_db

# 定義 API 路由，前綴為空，標籤為 "ask"
router = APIRouter(prefix="", tags=["ask"])


@router.post("/ask")
async def ask(input: AskRequest, db: Session = Depends(get_db)):
    """
    處理來自用戶的純文本提問請求。
    使用多租戶 RAG 進行文本查詢。
    """
    # 獲取 company_id
    company_id = input.company_id

    def generate():
        try:
            # 從訊息中提取最後一個用戶問題
            user_query = None
            for message in reversed(input.messages):
                if message.role == "user":
                    user_query = message.content
                    break

            if not user_query:
                raise ValueError("No user query found in messages")

            # 使用多租戶 RAG 服務進行查詢
            import asyncio

            async def query_with_company():
                multitenant_rag = get_multitenant_rag_service()
                rag_service = await multitenant_rag.get_company_rag_service(
                    company_id, db
                )
                return await rag_service.query_text(user_query, mode="hybrid")

            answer = asyncio.run(query_with_company())

            # 發送答案內容
            yield f"data: {json.dumps({'type': 'text', 'text': answer})}\n\n"

            # 發送結束標記
            yield "data: [DONE]\n\n"

        except Exception as e:
            # 發送錯誤訊息
            yield f"data: {json.dumps({'type': 'text', 'text': f'生成回應時發生錯誤: {str(e)}'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/ask/multimodal")
async def ask_multimodal(input: MultimodalAskRequest, db: Session = Depends(get_db)):
    """
    處理包含多模態內容的提問請求。
    使用 OCR RAG 進行多模態查詢。
    """
    # 獲取 company_id
    company_id = input.company_id

    def generate():
        try:
            # 從訊息中提取最後一個用戶問題
            user_query = None
            for message in reversed(input.messages):
                if message.role == "user":
                    user_query = message.content
                    break

            if not user_query:
                raise ValueError("No user query found in messages")

            # 使用多租戶 OCR RAG 服務進行查詢
            import asyncio

            async def query_with_company():
                multitenant_rag = get_multitenant_rag_service()
                rag_service = await multitenant_rag.get_company_rag_service(
                    company_id, db
                )
                # OCR RAG 將多模態內容作為一般文本查詢處理
                return await rag_service.query_text(user_query, mode="hybrid")

            answer = asyncio.run(query_with_company())

            # 發送答案內容
            yield f"data: {json.dumps({'type': 'text', 'text': answer})}\n\n"

            # 發送結束標記
            yield "data: [DONE]\n\n"

        except Exception as e:
            # 發送錯誤訊息
            yield f"data: {json.dumps({'type': 'text', 'text': f'多模態查詢發生錯誤: {str(e)}'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
