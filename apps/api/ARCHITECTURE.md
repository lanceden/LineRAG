# LineRAG API 架構說明

這份文件說明目前 LineRAG/apps/api 的服務架構、資料流與各模組職責，協助你快速理解與維護。

---

## 為什麼要重構

原本 `main.py` 將「設定、初始化、路由、業務邏輯、外部服務呼叫」混在一起：

- 測試困難、耦合度高、職責不清
- 設定硬編碼、無法輕易換環境
- 全域狀態過多，不易維護

重構後的目標：

- 清楚的分層：設定/日誌、服務、路由、（可選）資料存取
- 避免全域狀態，集中初始化與依賴注入
- 統一配置來源（環境變數），易於部署與擴充

---

## 高層次概觀

```bash
   ┌───────────────┐    ┌────────────────────┐
   │   Routers     │──▶ │     Services       │ ──▶ 外部系統
   │ (FastAPI)     │    │ (VectorStore/LLM/  │     - Qdrant (向量庫)
   │               │    │  RAG/Multimodal)   │     - vLLM/OpenAI (LLM)
   └──────┬────────┘    └───────────┬────────┘     - File System / S3（上傳）
          │                         │
          ▼                         ▼
     app/core                 app/core/logging
   （設定/環境）                  （日誌）
```

---

## 目錄結構（重點）

```bash
LineRAG/apps/api/
├─ main.py                         # FastAPI 入口：啟動初始化 + 掛載 routers
├─ ARCHITECTURE.md                 # 本文件
└─ app/
   ├─ core/
   │  ├─ config.py                 # 設定集中：環境變數/預設值
   │  └─ logging.py                # 統一 logging 設定
   ├─ schemas/
   │  ├─ ask.py                    # AskRequest / Message 等 Pydantic 模型
   │  ├─ ingest.py                 # IngestRequest
   │  └─ image.py                  # ImageQuestionRequest
   ├─ services/
   │  ├─ llm.py                    # LLM 客戶端（vLLM/OpenAI 兼容）
   │  ├─ vectorstore.py            # Embeddings + Qdrant 初始化與存取
   │  ├─ rag.py                    # 檢索 + 提示詞組裝 + 生成
   │  ├─ multimodal_service.py     # 多模態處理（圖像理解/OCR）
   │  └─ document_processor.py     # PDF/Word -> 圖片 -> OCR
   ├─ routers/
   │  ├─ health.py                 # 根路由與健康檢查
   │  ├─ ask.py                    # /ask（RAG 問答）
   │  ├─ ingest.py                 # /ingest（同步）、/ingest-async（背景任務）、/documents、刪除
   │  ├─ image.py                  # /ask-image、/ocr-extract、/upload-image
   │  └─ webhook.py                # LINE webhook（含簽名驗證）
   └─ repositories/                #（目前保留，不再使用 doc_index.json）
```

---

## 啟動流程（lifecycle）

- `main.py` 啟動時：
  - 初始化 logging
  - 在 `startup` 事件初始化 VectorStore（Embeddings + Qdrant 連線）
  - 掛載各個 router
- LLM 客戶端（`app/services/llm.py`）在載入時設定 API Base/Key
- 多模態服務（`app/services/multimodal_service.py`）延遲載入模型，第一次使用才載入

---

## 設定（環境變數）

由 `app/core/config.py` 管理，可由環境變數覆蓋，常用鍵值：

- OpenAI / vLLM
  - `OPENAI_API_BASE`（預設 `http://localhost:8001/v1`）
  - `OPENAI_API_KEY`（預設 `not-needed`）
  - `LLM_MODEL_NAME`（預設 `TheBloke/Qwen2-7B-Chat-AWQ`）
- Embeddings / Qdrant
  - `EMBEDDING_MODEL_NAME`（預設 `BAAI/bge-m3`）
  - `USE_LOCAL_QDRANT`（預設 `true`）
  - `QDRANT_PATH`（預設 `./local_qdrant`）或 `QDRANT_HOST`/`QDRANT_PORT`
  - `COLLECTION_NAME`（預設 `documents`）
- LINE
  - `LINE_CHANNEL_ACCESS_TOKEN`、`LINE_CHANNEL_SECRET`
- 上傳
  - `UPLOAD_IMAGE_DIR`（預設 `./uploads/images`）

---

## 服務層職責（Services）

- `vectorstore.py`
  - 建立 `HuggingFaceEmbeddings`
  - 依設定連線本地或遠端 Qdrant
  - 封裝 `langchain_community.vectorstores.Qdrant` 並提供 `retriever`
- `llm.py`
  - 統一與 OpenAI/vLLM 相容的 `chat(messages)` 介面
- `rag.py`
  - `build_prompt()`：整理對話訊息
  - `build_rag_prompt()`：把檢索到的段落組成提示詞
  - `generate_answer_from_messages()`：檢索 + 生成的整合流程
- `multimodal_service.py`
  - 多模態模型載入（延遲）
  - `process_image_with_text()`、`extract_text_from_image()`、`analyze_equipment_image()`
- `document_processor.py`
  - `pdf_to_images()`、`word_to_images()`：將 PDF/Word 轉為圖片
  - `process_document_with_ocr()`：整體管線（圖片 → OCR → 文本）

---

## 路由職責（Routers）

- `health.py`
  - `GET /`：存活訊息
  - `GET /health`：回報向量庫/檢索/多模態/LLM 狀態，並嘗試小型檢索以驗證可用性
- `ask.py`
  - `POST /ask`：呼叫 RAG 流程 → 回答文字
- `ingest.py`
  - `POST /ingest`：同步處理文件 → 切塊 → 寫入 Qdrant
  - `POST /ingest-async`：提交背景任務，立即回傳 `task_id`
  - `GET /tasks/{task_id}`：查任務狀態（demo 為記憶體暫存，商用請使用佇列/Redis）
  - `GET /documents`：從 Qdrant 的 payload.metadata 彙整文件清單（單一資料來源，不再使用 JSON）
  - `DELETE /documents/{doc_id}`：以 Qdrant Filter(metadata.doc_id) 刪除
- `image.py`
  - `POST /ask-image`：圖片問答（多模態）
  - `POST /ocr-extract`：從圖片擷取文字（多模態）
  - `POST /upload-image`：儲存圖片（目錄可設定）
- `webhook.py`
  - `POST /webhook`：LINE 回呼，包含 `X-Line-Signature` 驗簽

---

## 資料流與邏輯

### 1) Ingest（同步/非同步）

1. 驗證檔案存在與格式（pdf/doc/docx）
2. 擷取內容
   - 傳統：`PyMuPDFLoader`（PDF）或 `Docx2txt/UnstructuredWordDocumentLoader`（Word）
   - OCR：`document_processor` 先轉圖片，再以多模態模型提取文字
3. 分塊：`RecursiveCharacterTextSplitter(chunk_size=1000, overlap=200)`
4. 寫入 Qdrant：
   - 每個 chunk 帶有 metadata：
     ```json
     {
       "doc_id": "<uuid>",
       "filename": "原始文件名",
       "upload_time": 1730000000,
       "chunk_count": 24,
       "processing_method": "ocr|traditional",
       "page_number": 1
     }
     ```
5. 列表與刪除：
   - `/documents` 透過 scroll 彙整 `doc_id` → 文件清單
   - 刪除則以 Filter(metadata.doc_id) 直接刪除 Qdrant points

> 建議：為 `metadata.doc_id`、`metadata.filename` 建立 payload 索引；資料量大時改為分頁 + 條件查詢。

### 2) RAG /ask

1. `AskRequest` → `build_prompt()` 抽取用戶訊息
2. `retriever.get_relevant_documents()` 檢索相關段落
3. `build_rag_prompt()` 將段落嵌入提示詞
4. `llm.chat()` 生成答案

### 3) 多模態 /ask-image, /ocr-extract

- 延遲載入多模態模型（第一次呼叫才載入）
- 根據 prompt（OCR 或器材分析）產生回覆

---

## 日誌與健康檢查

- 日誌：
  - `app/core/logging.py` 設定全域 logging（可由 `LOG_LEVEL` 控制）
  - services 以命名 logger 記錄（`linerag.*`）
- 健康：
  - `GET /health` 報告向量庫/檢索/多模態/LLM 等狀態
  - 可再拆 `readiness` 與 `liveness` 以對接容器/編排系統

---

## 安全與商用提醒

- Webhook 已加入 `X-Line-Signature` 驗簽；需要設定 `LINE_CHANNEL_SECRET`
- 建議為管理端點（/ingest、/documents 刪除）加入 API Key/JWT 保護
- 上傳端點請增加檔案大小限制、檔名清理、檔案指紋掃描（生產環境）
- CORS 白名單、HTTPS 與憑證更新策略

---

## 如何執行

在 `LineRAG/apps/api` 目錄下：

```bash
uvicorn main:app --reload
```

> 注意：為了正確匯入 `app.services.*`，請在 `apps/api` 目錄啟動。

---

## 常見問題（FAQ）

- 為什麼 `from app.services.multimodal_service import ...`？
  - 因為多模態與 OCR 已被移入 `app/services`，統一由 `app` 作為套件根。

- `/documents` 為何不用 JSON？
  - 重構後以 Qdrant 的 payload.metadata 作為單一真實來源，避免多份狀態不同步。

- `/ingest-async` 的任務狀態是持久的嗎？
  - 目前示範為記憶體暫存。生產請改用任務佇列（Celery/RQ/Arq）與持久化（Redis/DB）。

---

## 後續可選強化

- API 認證/授權與速率限制
- LLM/Qdrant 呼叫的 timeout/重試/斷路器
- Prometheus /metrics、結構化日誌與分散式追蹤（OpenTelemetry）
- 將多模態/LLM 推理服務化（獨立服務）
- `/documents` 分頁化與條件過濾（大資料量場景）
