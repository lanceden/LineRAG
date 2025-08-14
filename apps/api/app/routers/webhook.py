import hmac
import hashlib
import base64
import os
from fastapi import APIRouter, Request, HTTPException, Depends
import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.schemas.ask import Message
from app.services.multitenant_rag import get_multitenant_rag_service
from app.services.multitenant_user import get_multitenant_user_service
from app.core.database import get_db

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
async def line_webhook(request: Request, db: Session = Depends(get_db)):
    """
    處理來自 LINE 的 Webhook 事件（多租戶版本）。
    根據 Channel Token 識別公司，使用該公司的 RAG 服務處理訊息。
    """
    raw_body = await request.body()
    signature = request.headers.get("x-line-signature")
    
    body = await request.json()
    events = body.get("events", [])

    # 取得多租戶服務
    multitenant_rag_service = get_multitenant_rag_service()
    user_service = get_multitenant_user_service(db)

    for event in events:
        if (
            event.get("type") == "message"
            and event.get("message", {}).get("type") == "text"
        ):
            user_text = event["message"]["text"]
            reply_token = event["replyToken"]
            line_user_id = event["source"]["userId"]

            try:
                # 根據請求頭中的 Channel Token 或從資料庫查找對應公司
                # 這裡需要實作根據 webhook 識別公司的邏輯
                # 暫時使用環境變數作為備用
                line_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
                
                if not line_access_token:
                    continue  # 如果 LINE token 未配置，則跳過

                # 驗證簽名（根據公司的 Channel Secret）
                if not verify_line_signature(raw_body, signature):
                    raise HTTPException(status_code=401, detail="Invalid LINE signature")

                # TODO: 實作根據 Channel Token 找到公司的邏輯
                # company = await multitenant_rag_service.get_company_by_line_channel(line_access_token, db)
                
                # 暫時使用預設公司 ID
                company_id = 1  # 這應該從上面的邏輯取得
                
                # 取得或建立用戶
                user = await user_service.get_user_by_line_id(line_user_id, company_id)
                if not user:
                    # 自動註冊新用戶
                    user = await user_service.create_user(
                        company_id=company_id,
                        line_id=line_user_id,
                        name=f"LINE用戶_{line_user_id[-6:]}",
                        role="user"
                    )

                # 取得該公司的 RAG 服務
                company_rag_service = await multitenant_rag_service.get_company_rag_service(company_id, db)
                
                # 使用公司的 RAG 服務生成答案
                answer = await company_rag_service.ask(user_text)

                # 記錄審計日誌
                await user_service.log_audit(
                    company_id=company_id,
                    user_id=user.id,
                    action="line_message_processed",
                    resource_type="message",
                    resource_id=reply_token,
                    status="success"
                )

                # 回覆訊息
                headers = {
                    "Authorization": f"Bearer {line_access_token}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "replyToken": reply_token,
                    "messages": [{"type": "text", "text": answer}],
                }
                
                async with httpx.AsyncClient() as client:
                    await client.post(LINE_REPLY_ENDPOINT, headers=headers, json=payload)

            except Exception as e:
                # 記錄錯誤日誌
                await user_service.log_audit(
                    company_id=company_id if 'company_id' in locals() else None,
                    action="line_message_error",
                    resource_type="message",
                    resource_id=reply_token,
                    status="error",
                    error_message=str(e)
                )
                continue

    return "ok"
