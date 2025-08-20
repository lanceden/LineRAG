import hmac
import hashlib
import base64
import os
import logging
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, Depends
import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.schemas.ask import Message
from app.services.multitenant_rag import get_multitenant_rag_service
from app.services.multitenant_user import get_multitenant_user_service
from app.services.company_service import CompanyService
from app.models.company import Company
from app.core.database import get_db

load_dotenv()

# 設定日誌
logger = logging.getLogger("webhook")

# 定義 API 路由，前綴為空，標籤為 "webhook"
router = APIRouter(prefix="", tags=["webhook"])

# 從環境變數讀取 LINE API endpoint
LINE_REPLY_ENDPOINT = os.getenv(
    "LINE_REPLY_ENDPOINT", "https://api.line.me/v2/bot/message/reply"
)


def verify_line_signature_for_company(
    body: bytes,
    x_line_signature: str | None,
    channel_secret: str,
    debug: bool = True,
    skip_verification: bool = False,
) -> bool:
    """
    驗證來自 LINE 的請求簽名（使用指定公司的 Channel Secret）。
    使用指定的 Channel Secret 計算 HMAC-SHA256 簽名，並與請求頭中的簽名進行比較。
    """
    # 臨時跳過簽名驗證（僅用於調試）
    if skip_verification:
        if debug:
            logger.warning("⚠️ 跳過 LINE 簽名驗證 (調試模式)")
        return True

    if debug:
        logger.info(f"🔐 簽名驗證調試:")
        logger.info(
            f"   Channel Secret: {'已設定' if channel_secret else '未設定'} (長度: {len(channel_secret) if channel_secret else 0})"
        )
        # 顯示 Channel Secret 的前幾個字符用於調試
        logger.info(
            f"   Channel Secret 前綴: {channel_secret[:8] if channel_secret else 'None'}..."
        )
        logger.info(
            f"   請求簽名: {x_line_signature[:30] if x_line_signature else 'None'}..."
        )
        logger.info(f"   請求體長度: {len(body)} bytes")
        # 顯示請求體的前幾個字符
        logger.info(f"   請求體前綴: {body[:50].decode('utf-8', errors='ignore')}...")

    if not channel_secret or not x_line_signature:
        if debug:
            logger.warning(f"❌ 簽名驗證失敗: Channel Secret 或簽名為空")
        return False

    mac = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("utf-8")

    if debug:
        logger.info(f"   計算出的簽名: {expected[:30]}...")
        logger.info(
            f"   簽名匹配: {'✅' if hmac.compare_digest(expected, x_line_signature) else '❌'}"
        )

    return hmac.compare_digest(expected, x_line_signature)


@router.post("/webhook")
async def line_webhook(request: Request, db: Session = Depends(get_db)):
    """
    處理來自 LINE 的 Webhook 事件（多租戶版本）。
    根據 Channel Token 識別公司，使用該公司的 RAG 服務處理訊息。
    """
    logger.info("🔔 收到 LINE Webhook 請求")

    try:
        raw_body = await request.body()
        signature = request.headers.get("x-line-signature")

        logger.info(f"📝 請求簽名: {signature[:20] if signature else 'None'}...")
        logger.info(f"📦 請求體大小: {len(raw_body)} bytes")

        try:
            body = await request.json()
            events = body.get("events", [])
            logger.info(f"🎯 收到 {len(events)} 個事件")
        except Exception as e:
            logger.error(f"❌ 解析請求體失敗: {e}")
            return "error"

    except Exception as e:
        if "ClientDisconnect" in str(e):
            logger.warning(f"⚠️ 客戶端斷開連接: {e}")
            return "client_disconnected"
        else:
            logger.error(f"❌ 讀取請求體失敗: {e}")
            return "error"

    # 取得多租戶服務
    multitenant_rag_service = get_multitenant_rag_service()
    user_service = get_multitenant_user_service(db)

    for i, event in enumerate(events):
        logger.info(f"🔄 處理事件 {i+1}/{len(events)}: {event.get('type', 'unknown')}")

        if (
            event.get("type") == "message"
            and event.get("message", {}).get("type") == "text"
        ):
            user_text = event["message"]["text"]
            reply_token = event["replyToken"]
            line_user_id = event["source"]["userId"]

            logger.info(f"💬 收到文字訊息: '{user_text}' from {line_user_id}")
            logger.info(f"🎫 Reply Token: {reply_token}")

            try:
                # 正確的多租戶邏輯：根據 Channel Token 識別公司
                # 從環境變數獲取當前的 Channel Token
                line_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

                if not line_access_token:
                    logger.error("❌ LINE_CHANNEL_ACCESS_TOKEN 環境變數未設定")
                    continue

                # 根據 Channel Token 找到對應的公司
                company = (
                    db.query(Company)
                    .filter(
                        Company.line_channel_token == line_access_token,
                        Company.is_active == True,
                        Company.line_bot_enabled == True,
                    )
                    .first()
                )

                if not company:
                    logger.error(
                        f"❌ 找不到對應的公司，Channel Token: {line_access_token[:20]}..."
                    )
                    continue

                logger.info(f"✅ 識別到公司: {company.name} (ID: {company.id})")

                # 使用該公司的 Channel Secret 驗證簽名
                if not verify_line_signature_for_company(
                    raw_body, signature, company.line_channel_secret
                ):
                    logger.error(f"❌ LINE 簽名驗證失敗，公司: {company.name}")
                    continue

                logger.info(
                    f"✅ LINE 簽名驗證成功，公司: {company.name}"
                )  # 找不到匹配的公司或簽名驗證失敗

                company_id = company.id
                line_access_token = company.line_channel_token

                # 取得或建立用戶
                user = await user_service.get_user_by_line_id(line_user_id, company_id)
                if not user:
                    # 自動註冊新用戶
                    user = await user_service.create_user(
                        company_id=company_id,
                        line_id=line_user_id,
                        name=f"LINE用戶_{line_user_id[-6:]}",
                        role="user",
                    )

                # 取得該公司的 RAG 服務
                logger.info(f"🤖 取得公司 {company.name} 的 RAG 服務")
                company_rag_service = (
                    await multitenant_rag_service.get_company_rag_service(
                        company_id, db
                    )
                )

                # 使用公司的 RAG 服務生成答案
                logger.info(f"🔍 開始處理問題: '{user_text}'")

                # 添加調試：檢查 RAG 系統狀態
                try:
                    # 檢查 RAG 系統是否已初始化
                    logger.info(
                        f"🔧 RAG 系統初始化狀態: {company_rag_service.initialized}"
                    )

                    # 檢查公司專用工作目錄
                    if (
                        hasattr(company_rag_service, "company_working_dir")
                        and company_rag_service.company_working_dir
                    ):
                        working_dir = company_rag_service.company_working_dir
                        logger.info(f"📁 公司專用工作目錄: {working_dir}")
                    else:
                        working_dir = os.getenv("RAG_WORKING_DIR", "./rag_storage")
                        logger.info(f"📁 預設工作目錄: {working_dir}")

                    # 檢查目錄是否存在及內容
                    if os.path.exists(working_dir):
                        files = list(Path(working_dir).rglob("*"))
                        logger.info(f"📂 工作目錄檔案數量: {len(files)}")
                        if files:
                            logger.info(f"📄 部分檔案: {[f.name for f in files[:5]]}")
                    else:
                        logger.warning(f"⚠️ 工作目錄不存在: {working_dir}")

                    # 檢查公司 ID
                    if hasattr(company_rag_service, "company_id"):
                        logger.info(
                            f"🏢 RAG 服務公司 ID: {company_rag_service.company_id}"
                        )

                except Exception as e:
                    logger.warning(f"⚠️ RAG 系統狀態檢查失敗: {e}")

                # 使用 RAG-Anything 進行文本查詢
                answer = await company_rag_service.query_text(
                    user_text, mode="hybrid", company_id=str(company_id)
                )
                logger.info(f"💡 生成答案: '{answer[:100]}...' (長度: {len(answer)})")

                # 記錄審計日誌
                await user_service.log_audit(
                    company_id=company_id,
                    user_id=user.id,
                    action="line_message_processed",
                    resource_type="message",
                    resource_id=reply_token,
                    status="success",
                )

                # 回覆訊息
                logger.info(f"📤 準備回覆訊息給 LINE 用戶")
                headers = {
                    "Authorization": f"Bearer {line_access_token}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "replyToken": reply_token,
                    "messages": [{"type": "text", "text": answer}],
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        LINE_REPLY_ENDPOINT, headers=headers, json=payload
                    )
                    if response.status_code == 200:
                        logger.info("✅ 成功回覆 LINE 訊息")
                    else:
                        logger.error(
                            f"❌ LINE 回覆失敗: {response.status_code} - {response.text}"
                        )

            except Exception as e:
                logger.error(f"💥 處理 LINE 訊息時發生錯誤: {e}")
                # 記錄錯誤日誌
                await user_service.log_audit(
                    company_id=company_id if "company_id" in locals() else None,
                    action="line_message_error",
                    resource_type="message",
                    resource_id=reply_token,
                    status="error",
                    error_message=str(e),
                )
                continue
        else:
            logger.info(f"⏭️ 跳過非文字訊息事件: {event.get('type', 'unknown')}")

    logger.info("🏁 Webhook 處理完成")
    return "ok"
