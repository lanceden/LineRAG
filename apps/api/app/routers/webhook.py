import hmac
import hashlib
import base64
import os
from fastapi import APIRouter, Request, HTTPException
import httpx
from dotenv import load_dotenv

from app.schemas.ask import Message
from app.services.rag import generate_answer_from_messages

load_dotenv()

# 定義 API 路由，前綴為空，標籤為 "webhook"
router = APIRouter(prefix="", tags=["webhook"])

# 從環境變數讀取 LINE API endpoint
LINE_REPLY_ENDPOINT = os.getenv(
    "LINE_REPLY_ENDPOINT", "https://api.line.me/v2/bot/message/reply"
)


def verify_line_signature(body: bytes, x_line_signature: str | None) -> bool:
    """
    驗證來自 LINE 的請求簽名。
    使用 LINE Channel Secret 計算 HMAC-SHA256 簽名，並與請求頭中的簽名進行比較。
    如果未配置 LINE Channel Secret，則跳過驗證（用於開發環境）。
    """
    secret = os.getenv("LINE_CHANNEL_SECRET")
    if not secret:
        # 如果沒有配置 secret，則跳過驗證（開發環境）
        return True
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(expected, x_line_signature or "")


@router.post("/webhook")
async def line_webhook(request: Request):
    """
    處理來自 LINE 的 Webhook 事件。
    驗證請求簽名，解析事件，並對文字訊息進行回覆。
    """
    raw_body = await request.body()
    signature = request.headers.get("x-line-signature")
    if not verify_line_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid LINE signature")

    body = await request.json()
    events = body.get("events", [])

    for event in events:
        if (
            event.get("type") == "message"
            and event.get("message", {}).get("type") == "text"
        ):
            user_text = event["message"]["text"]
            reply_token = event["replyToken"]

            # 使用 RAG 服務生成答案
            answer = generate_answer_from_messages(
                [
                    Message(
                        id="1", role="user", parts=[{"type": "text", "text": user_text}]
                    )
                ]
            )

            line_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
            if not line_access_token:
                continue  # 如果 LINE token 未配置，則跳過

            headers = {
                "Authorization": f"Bearer {line_access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": answer}],
            }
            # 使用 httpx 發送回覆訊息
            async with httpx.AsyncClient() as client:
                await client.post(LINE_REPLY_ENDPOINT, headers=headers, json=payload)

    return "ok"
