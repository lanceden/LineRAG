from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

from app.schemas.ask import AskRequest
from app.services.rag import generate_answer_from_messages

# 定義 API 路由，前綴為空，標籤為 "ask"
router = APIRouter(prefix="", tags=["ask"])


@router.post("/ask")
def ask(input: AskRequest):
    """
    處理來自用戶的提問請求。
    接收包含訊息列表的 AskRequest 物件，
    調用 generate_answer_from_messages 服務生成答案，
    並返回 Server-Sent Events 格式的流式回應。
    """
    def generate():
        try:
            answer = generate_answer_from_messages(input.messages)
            
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
        }
    )
