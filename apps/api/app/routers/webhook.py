import hmac
import hashlib
import base64
import os
import logging
import time
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
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


# 客服口吻重寫：將 RAG 原始答案改寫為客服風格（使用 OpenAI 相容 API）
# 中文註解：若無 OPENAI_API_KEY 或發生錯誤，將回傳原始答案，確保不中斷
import json


# 中文註解：判斷是否為結構化輸出（JSON / 程式碼塊 / 表格等），若是則避免重寫以免破壞格式
def looks_structured(text: str) -> bool:
    # 嘗試解析 JSON
    try:
        json.loads(text)
        return True
    except Exception:
        pass
    # 程式碼塊（含 ```）
    if "```" in text:
        return True
    # 簡易表格樣式（管線符 + 分隔線）
    if "|" in text and "---" in text:
        return True
    return False


async def rewrite_to_cs_tone(user_query: str, rag_answer: str) -> str:
    # 快速檢查：如果答案很短或包含特定關鍵字，直接返回（避免不必要的 API 調用）
    if len(rag_answer.strip()) < 50 or any(
        keyword in rag_answer.lower()
        for keyword in ["對不起", "抱歉", "錯誤", "無法", "沒有找到", "系統錯誤"]
    ):
        logger.info("⚡ 跳過重寫：答案太短或包含錯誤訊息")
        return rag_answer

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("REWRITE_MODEL", "gpt-3.5-turbo")  # 改用更快的模型

    # 若未設定 API Key，直接返回原文
    if not api_key:
        logger.warning("⚠️ 未設定 OPENAI_API_KEY，跳過客服口吻重寫")
        return rag_answer

    system_prompt = (
        "你是運動歐巴系統的客服助理，正在直接與運動中心會員對話。\n"
        "回覆風格：自然親切、直接回答，避免套模板。\n"
        "重要提醒：\n"
        "- 你就是客服，不要說「可以聯繫客服」或「聯繫我們的客服團隊」\n"
        "- 這裡的用戶都是運動中心的會員，不是公司員工\n"
        "- 請假是指會員課程請假，不是員工請假\n"
        "- 直接回答問題，不要每次都說「我了解您...」\n"
        "- 結尾可以說「有其他問題可以繼續問我」而不是「聯繫客服」\n"
        "- 保持內容準確，不要改動數字和專有名詞\n"
        "用第一人稱回應，就像你親自在服務這位會員。"
    )
    user_prompt = (
        f"用戶問題：{user_query}\n"
        f"RAG原始答案（內容正確，但需改寫口吻）：\n{rag_answer}\n"
        "請依系統要求重寫。"
    )

    # 若為結構化輸出，避免重寫以免破壞格式
    if looks_structured(rag_answer):
        return rag_answer

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions", headers=headers, json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if not content:
                logger.warning("⚠️ 重寫服務回應內容為空，改用原文")
                return rag_answer
            return content.strip()
    except Exception as e:
        logger.warning(f"⚠️ 回覆重寫失敗：{e}，改用原文")
        return rag_answer


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
async def line_webhook(
    request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    處理來自 LINE 的 Webhook 事件（多租戶 + 多線程版本）。
    支援文字和圖片訊息，使用背景任務並行處理。
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

    # 不在這裡取得服務，改在背景處理函數中取得
    # 避免重複取得和不必要的資源佔用

    for i, event in enumerate(events):
        logger.info(f"🔄 處理事件 {i+1}/{len(events)}: {event.get('type', 'unknown')}")

        if event.get("type") == "message" and event.get("message", {}).get("type") in [
            "text",
            "image",
        ]:
            message = event["message"]
            message_type = message["type"]
            reply_token = event["replyToken"]
            line_user_id = event["source"]["userId"]

            if message_type == "text":
                user_text = message["text"]
                user_images = None
                logger.info(f"💬 收到文字訊息: '{user_text}' from {line_user_id}")
            elif message_type == "image":
                user_text = "用戶上傳了圖片，請分析圖片內容"  # 默認查詢文字
                image_id = message["id"]
                user_images = [{"image_id": image_id}]  # 準備圖片數據
                logger.info(f"🖼️ 收到圖片訊息: image_id={image_id} from {line_user_id}")

            logger.info(f"🎫 Reply Token: {reply_token}")

            # 去重保險 1：檢查 LINE 平台重送事件，但允許正常重送處理
            is_redelivery = event.get("deliveryContext", {}).get("isRedelivery", False)
            if is_redelivery:
                logger.info("ℹ️ 檢測到 isRedelivery=True，這是 LINE 的重送機制")
                # 不直接跳過，讓後續的 replyToken 去重處理

            # 去重保險 2：以 replyToken 做去重，若已處理成功則跳過
            try:
                # 延遲載入，避免循環引用；若頂部已匯入會自動覆用
                from app.models.audit import AuditLog  # type: ignore

                existing_log = (
                    db.query(AuditLog)
                    .filter(
                        AuditLog.action == "line_message_processed",
                        AuditLog.resource_type == "message",
                        AuditLog.resource_id == reply_token,
                    )
                    .first()
                )
                if existing_log:
                    logger.info(
                        "⏭️ 該 replyToken 已記錄處理成功（line_message_processed），跳過重複事件"
                    )
                    continue
            except Exception as _e:
                # 去重檢查失敗不影響主流程，避免漏回覆
                logger.warning(f"⚠️ 去重檢查失敗：{_e}（將繼續處理以避免漏回覆）")

            # 將處理邏輯移到背景任務，實現多線程並行處理
            background_tasks.add_task(
                process_line_message_async,
                event,
                raw_body,
                signature,
                user_text,
                user_images,
                reply_token,
                line_user_id,
            )

        else:
            logger.info(f"⏭️ 跳過非文字/圖片訊息事件: {event.get('type', 'unknown')}")

    logger.info("🏁 Webhook 處理完成 (已加入背景處理隊列)")
    return "ok"


async def process_line_message_async(
    event: dict,
    raw_body: bytes,
    signature: str,
    user_text: str,
    user_images: list,
    reply_token: str,
    line_user_id: str,
):
    """背景處理 LINE 訊息 - 支援圖片 + 多線程並行處理"""

    try:
        # 重新建立資料庫連接（BackgroundTasks 需要）
        from app.core.database import SessionLocal

        db = SessionLocal()

        try:
            # 取得多租戶服務
            multitenant_rag_service = get_multitenant_rag_service()
            user_service = get_multitenant_user_service(db)

            # 多租戶邏輯：根據 LINE User ID 找到對應的公司
            logger.info(f"🔍 根據 LINE User ID 查找公司: {line_user_id}")

            # 先嘗試從已存在的用戶記錄中找到公司
            from app.models.tenant_user import TenantUser

            existing_user = (
                db.query(TenantUser).filter(TenantUser.line_id == line_user_id).first()
            )

            company = None
            line_access_token = None

            if existing_user:
                # 從現有用戶記錄獲取公司
                company = (
                    db.query(Company)
                    .filter(
                        Company.id == existing_user.company_id,
                        Company.is_active == True,
                        Company.line_bot_enabled == True,
                    )
                    .first()
                )
                if company:
                    line_access_token = company.line_channel_token
                    logger.info(
                        f"✅ 從現有用戶找到公司: {company.name} (ID: {company.id})"
                    )

            # 如果沒有找到現有用戶，則遍歷公司進行簽名驗證（新用戶註冊）
            if not company:
                logger.info("🔍 用戶不存在，嘗試簽名驗證識別公司")
                companies = (
                    db.query(Company)
                    .filter(
                        Company.is_active == True,
                        Company.line_bot_enabled == True,
                        Company.line_channel_secret.isnot(None),
                        Company.line_channel_token.isnot(None),
                    )
                    .all()
                )

                for test_company in companies:
                    if verify_line_signature_for_company(
                        raw_body,
                        signature,
                        test_company.line_channel_secret,
                        debug=False,
                    ):
                        company = test_company
                        line_access_token = test_company.line_channel_token
                        logger.info(
                            f"✅ 透過簽名驗證識別公司: {company.name} (ID: {company.id})"
                        )
                        break
            else:
                # 驗證現有公司的簽名
                if not verify_line_signature_for_company(
                    raw_body, signature, company.line_channel_secret, debug=False
                ):
                    logger.error(f"❌ 公司 {company.name} 的簽名驗證失敗")
                    return

            if not company:
                logger.error("❌ 找不到對應的公司")
                return

            company_id = company.id

            # 取得或建立用戶
            user = await user_service.get_user_by_line_id(line_user_id, company_id)
            if not user:
                user = await user_service.create_user(
                    company_id=company_id,
                    line_id=line_user_id,
                    name=f"LINE用戶_{line_user_id[-6:]}",
                    role="user",
                )

            # 取得該公司的 RAG 服務
            company_rag_service = await multitenant_rag_service.get_company_rag_service(
                company_id, db
            )

            # 執行查詢（支援圖片）
            if user_images:
                # 下載圖片內容
                multimodal_content = []
                for img_data in user_images:
                    try:
                        image_id = img_data["image_id"]
                        logger.info(f"📥 開始下載圖片: {image_id}")

                        # 從 LINE 下載圖片
                        image_url = f"https://api-data.line.me/v2/bot/message/{image_id}/content"
                        headers = {"Authorization": f"Bearer {line_access_token}"}

                        async with httpx.AsyncClient() as client:
                            img_response = await client.get(image_url, headers=headers)
                            if img_response.status_code == 200:
                                image_data = img_response.content
                                logger.info(
                                    f"✅ 成功下載圖片，大小: {len(image_data)} bytes"
                                )

                                # 轉換為 base64 用於多模態查詢
                                import base64

                                image_base64 = base64.b64encode(image_data).decode(
                                    "utf-8"
                                )
                                multimodal_content.append(
                                    {
                                        "type": "image",
                                        "data": image_base64,
                                        "format": "base64",
                                    }
                                )
                            else:
                                logger.error(
                                    f"❌ 圖片下載失敗: {img_response.status_code}"
                                )
                    except Exception as e:
                        logger.error(f"❌ 處理圖片時發生錯誤: {e}")

                # 多模態查詢
                logger.info(f"🔍 開始多模態查詢 (圖片+文字): '{user_text}'")
                answer = await company_rag_service.query_multimodal(
                    user_text,
                    multimodal_content=multimodal_content,
                    mode="naive",
                    company_id=str(company_id),
                )
            else:
                # 純文本查詢
                logger.info(f"🔍 開始文本查詢: '{user_text}'")
                answer = await company_rag_service.query_text(
                    user_text, mode="naive", company_id=str(company_id)
                )

            logger.info(f"💡 生成答案: '{answer[:100]}...' (長度: {len(answer)})")

            # 客服口吻重寫
            polished = await rewrite_to_cs_tone(user_text, answer)

            # 回覆 LINE 訊息
            headers = {
                "Authorization": f"Bearer {line_access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": polished}],
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

            # 記錄審計日誌
            await user_service.log_audit(
                company_id=company_id,
                user_id=user.id,
                action="line_message_processed",
                resource_type="message",
                resource_id=reply_token,
                status="success",
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"💥 背景處理 LINE 訊息時發生錯誤: {e}")
        try:
            if "db" in locals():
                db.close()
        except:
            pass
