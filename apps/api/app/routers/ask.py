"""Query API routes - adapted for independent folder architecture"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
from typing import Optional

from app.schemas.ask import AskRequest, MultimodalAskRequest
from app.services.document_lifecycle_manager import (
    DocumentLifecycleManager,
    get_document_lifecycle_manager,
)
from app.core.database import get_db

router = APIRouter(prefix="", tags=["ask"])


@router.post("/ask")
async def ask(input: AskRequest, db: Session = Depends(get_db)):
    """
    處理來自用戶的純文本提問請求。
    使用多租戶 RAG 進行文本查詢。
    """
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
                lifecycle_manager = get_document_lifecycle_manager()
                result = await lifecycle_manager.query_documents(
                    query=user_query, company_id=company_id, limit=10
                )

                if result["status"] == "success":
                    # Format results for streaming
                    if result["results"]:
                        return "\n\n".join(
                            [
                                f"Document: {r['doc_id']}\nContent: {r['content']}\nScore: {r['score']:.2f}"
                                for r in result["results"]
                            ]
                        )
                    else:
                        return "No relevant documents found."
                else:
                    return f"Query failed: {result.get('message', 'Unknown error')}"

            answer = asyncio.run(query_with_company())

            # Send answer content
            yield f"data: {json.dumps({'type': 'text', 'text': answer})}\n\n"

            # Send end marker
            yield "data: [DONE]\n\n"

        except Exception as e:
            # Send error message
            yield f"data: {json.dumps({'type': 'text', 'text': f'Error generating response: {str(e)}'})}\n\n"
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
    Handle multimodal question requests.
    Use document lifecycle manager for multimodal queries.
    """
    company_id = input.company_id

    def generate():
        try:
            # Extract the last user question from messages
            user_query = None
            for message in reversed(input.messages):
                if message.role == "user":
                    user_query = message.content
                    break

            if not user_query:
                raise ValueError("No user query found in messages")

            # Use document lifecycle manager for multimodal query
            import asyncio

            async def query_multimodal():
                lifecycle_manager = get_document_lifecycle_manager()

                # For multimodal, we can extend the query with multimodal content info
                enhanced_query = user_query
                if input.multimodal_content:
                    enhanced_query += (
                        f" [Multimodal content: {len(input.multimodal_content)} items]"
                    )

                result = await lifecycle_manager.query_documents(
                    query=enhanced_query, company_id=company_id, limit=10
                )

                if result["status"] == "success":
                    if result["results"]:
                        return "\n\n".join(
                            [
                                f"Document: {r['doc_id']}\nContent: {r['content']}\nScore: {r['score']:.2f}"
                                for r in result["results"]
                            ]
                        )
                    else:
                        return "No relevant documents found for multimodal query."
                else:
                    return f"Multimodal query failed: {result.get('message', 'Unknown error')}"

            answer = asyncio.run(query_multimodal())

            # Send answer content
            yield f"data: {json.dumps({'type': 'text', 'text': answer})}\n\n"

            # Send end marker
            yield "data: [DONE]\n\n"

        except Exception as e:
            # Send error message
            yield f"data: {json.dumps({'type': 'text', 'text': f'Multimodal query error: {str(e)}'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
