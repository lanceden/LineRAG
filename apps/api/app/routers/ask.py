from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
from typing import Optional

from app.schemas.ask import AskRequest, MultimodalAskRequest
from app.services.rag_anything import get_rag_service

# 定義 API 路由，前綴為空，標籤為 "ask"
router = APIRouter(prefix="", tags=["ask"])


@router.post("/ask")
async def ask(input: AskRequest):
    """
    處理來自用戶的純文本提問請求。
    使用 RAG-Anything 進行文本查詢。
    """
    rag_service = get_rag_service()

    if not rag_service.initialized:
        raise HTTPException(status_code=503, detail="RAG service not initialized")

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

            # 使用 RAG-Anything 進行查詢
            import asyncio

            answer = asyncio.run(rag_service.query_text(user_query, mode="hybrid"))

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
async def ask_multimodal(input: MultimodalAskRequest):
    """
    處理包含多模態內容的提問請求。
    使用 RAG-Anything 進行多模態查詢。
    """
    rag_service = get_rag_service()

    if not rag_service.initialized:
        raise HTTPException(status_code=503, detail="RAG service not initialized")

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

            # 使用 RAG-Anything 進行多模態查詢
            import asyncio

            answer = asyncio.run(
                rag_service.query_multimodal(
                    query=user_query,
                    multimodal_content=input.multimodal_content,
                    mode="hybrid",
                )
            )

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
