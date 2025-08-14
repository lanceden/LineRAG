# LineRAG API 架構說明 v2.0 - RAG-Anything 多租戶版本

本文件說明 LineRAG API v2.0 基於 RAG-Anything 框架的多租戶架構設計。

---

## 🏗️ 多租戶系統架構概覽

LineRAG API v2.0 採用完整的多租戶架構，支援多家公司共用一套系統：

```bash
┌─────────────────────────────────────────────────────────────────┐
│                    LineRAG Multi-Tenant API v2.0               │
├─────────────────────────────────────────────────────────────────┤
│                      FastAPI Application                       │
├─────────────────────────────────────────────────────────────────┤
│    Routers: health | ask | ingest | webhook | users | admin    │
├─────────────────────────────────────────────────────────────────┤
│                         Services                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ MultiTenant RAG  │  │ MultiTenant User │  │   Audit Log  │  │
│  │   Service        │  │    Service       │  │   Service    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     Data Storage Layer                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   PostgreSQL     │  │     Qdrant       │  │     Redis    │  │
│  │ (Multi-Tenant)   │  │ (Per Company)    │  │ (Sessions)   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    External Services                           │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │   OpenAI API     │  │  RAG-Anything    │                    │
│  │   (GPT-4o)       │  │   Framework      │                    │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 多租戶架構重構說明

### 為什麼採用多租戶架構？

**業務需求：**

- 一套系統支援多家公司共用
- 各公司資料完全隔離
- 統一管理後台降低維運成本
- 彈性的訂閱方案和配額管理

**技術優勢：**

- 資源共享，降低基礎設施成本
- 統一升級和維護
- 橫向擴展能力
- 標準化的多公司管理流程

**RAG-Anything 框架優勢：**

- 統一的多模態 RAG 框架
- 支援複雜文檔格式（PDF、Office、圖片、表格、公式）
- 內建 MinerU 解析器，提供最佳的文檔處理品質
- 按公司隔離的工作目錄設計

---

## 📁 多租戶目錄結構

```bash
LineRAG/apps/api/
├─ main.py                         # FastAPI 入口，多租戶初始化
├─ init_db.py                      # 資料庫初始化腳本
├─ ARCHITECTURE.md                 # 本文件
├─ requirements.txt                # 包含 PostgreSQL、SQLAlchemy 等依賴
├─ bak/                           # 舊架構的備份文件
└─ app/
   ├─ core/
   │  ├─ env.py                   # 環境變數配置
   │  ├─ logging.py               # 統一日誌配置  
   │  └─ database.py              # PostgreSQL 連接管理
   ├─ models/                     # 多租戶資料模型
   │  ├─ __init__.py              # 模型匯出
   │  ├─ company.py               # 公司/租戶模型
   │  ├─ user.py                  # 用戶模型（跨公司）
   │  ├─ document.py              # 文檔元資料模型
   │  └─ audit.py                 # 審計日誌模型
   ├─ schemas/
   │  ├─ ask.py                   # 問答請求/回應模型
   │  ├─ ingest.py                # 文檔上傳模型
   │  └─ user.py                  # 用戶相關模型
   ├─ services/
   │  ├─ rag_anything.py          # 基礎 RAG-Anything 服務
   │  ├─ multitenant_rag.py       # 多租戶 RAG 服務管理器
   │  └─ multitenant_user.py      # 多租戶用戶管理服務
   ├─ routers/
   │  ├─ health.py                # 系統健康檢查
   │  ├─ ask.py                   # 問答API（支援多租戶）
   │  ├─ ingest.py                # 文檔上傳和處理（按公司隔離）
   │  ├─ webhook.py               # LINE webhook（多公司路由）
   │  ├─ users.py                 # 用戶管理
   │  └─ admin.py                 # 管理功能
   └─ repositories/
      └─ document_index.py         # 文檔索引管理
```

---

## 🗄️ 多租戶資料模型設計

### 核心資料表

#### 1. Company（公司/租戶）

```python
class Company(Base):
    id = Integer (Primary Key)
    name = String(255)              # 公司名稱
    code = String(50)               # 公司代碼 (唯一)
    
    # LINE Channel 設定
    line_channel_token = Text       # LINE Channel Access Token
    line_channel_secret = String    # LINE Channel Secret
    line_bot_enabled = Boolean      # LINE 機器人是否啟用
    
    # 訂閱設定
    subscription_plan = String      # 訂閱方案 (standard/premium)
    max_documents = Integer         # 最大文檔數量
    max_queries_per_month = Integer # 每月查詢上限
    
    # RAG 設定
    rag_working_dir = String        # RAG 工作目錄
    storage_quota_gb = Integer      # 儲存配額
    
    # 狀態管理
    is_active = Boolean
    created_at = DateTime
    updated_at = DateTime
```

#### 2. User（用戶）

```python
class User(Base):
    id = Integer (Primary Key)
    company_id = ForeignKey(Company) # 所屬公司
    
    # LINE 用戶資訊
    line_id = String(255)           # LINE 用戶ID
    line_display_name = String      # LINE 顯示名稱
    
    # 系統用戶資訊
    name = String(255)              # 用戶姓名
    email = String(255)             # 電子郵件
    role = String(50)               # 角色: admin, cs, user
    
    # 統計資訊
    total_queries = Integer         # 總查詢次數
    monthly_queries = Integer       # 當月查詢次數
    last_login = DateTime           # 最後登入時間
```

#### 3. DocumentMetadata（文檔元資料）

```python
class DocumentMetadata(Base):
    id = Integer (Primary Key)
    company_id = ForeignKey(Company) # 所屬公司
    
    # 文檔基本資訊
    document_id = String(255)       # RAG系統中的文檔ID
    original_filename = String      # 原始檔名
    file_path = Text               # 檔案路徑
    file_size = BigInteger         # 檔案大小
    mime_type = String             # 檔案類型
    
    # 處理資訊
    processing_method = String      # 處理方法: auto, ocr
    processing_status = String      # 處理狀態
    chunk_count = Integer          # 分塊數量
    
    # 內容統計
    has_images = Boolean           # 是否包含圖片
    has_tables = Boolean           # 是否包含表格
    has_formulas = Boolean         # 是否包含公式
```

#### 4. AuditLog（審計日誌）

```python
class AuditLog(Base):
    id = Integer (Primary Key)
    company_id = ForeignKey(Company) # 所屬公司
    user_id = ForeignKey(User)       # 操作用戶
    
    # 操作資訊
    action = String(100)            # 操作類型
    resource_type = String(50)      # 資源類型
    resource_id = String(255)       # 資源ID
    
    # 請求資訊
    endpoint = String(255)          # API端點
    ip_address = String(45)         # IP地址
    user_agent = Text              # 用戶代理
    
    # 結果資訊
    status = String(20)            # 操作狀態
    response_time_ms = Integer     # 回應時間
    timestamp = DateTime           # 操作時間
```

---

## 🔧 多租戶服務層架構

### 1. MultiTenantRAGService

```python
class MultiTenantRAGService:
    """多租戶 RAG 服務管理器"""
    
    async def get_company_rag_service(company_id: int) -> RAGAnythingService:
        """取得指定公司的 RAG 服務實例"""
        
    async def get_company_by_line_channel(channel_token: str) -> Company:
        """根據 LINE Channel Token 找到對應的公司"""
        
    async def cleanup_company_service(company_id: int):
        """清理指定公司的 RAG 服務"""
```

**核心功能：**

- 按公司 ID 管理獨立的 RAG-Anything 實例
- 自動建立公司專用的工作目錄
- 快取服務實例，提升效能
- 支援服務清理和資源管理

### 2. MultiTenantUserService

```python
class MultiTenantUserService:
    """多租戶用戶管理服務"""
    
    async def get_user_by_line_id(line_id: str, company_id: int) -> User:
        """根據 LINE ID 取得用戶"""
        
    async def get_user_company(line_id: str) -> tuple[User, Company]:
        """取得用戶及其所屬公司"""
        
    async def check_user_permission(user_id: int, required_role: str) -> bool:
        """檢查用戶權限"""
        
    async def log_audit(company_id: int, action: str, **kwargs):
        """記錄審計日誌"""
```

**核心功能：**

- 跨公司的用戶身份驗證
- 角色權限管理（admin > cs > user）
- 完整的審計日誌記錄
- 用戶統計和配額管理

---

## 🚀 多租戶啟動流程

### 應用程式生命週期

1. **資料庫初始化 (`main.py`)**：

   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # 建立資料表
       create_tables()
       
       # 初始化多租戶 RAG 服務管理器
       multitenant_rag_service = get_multitenant_rag_service()
       
       yield
       
       # 清理所有租戶服務
       await multitenant_rag_service.cleanup_all_services()
   ```

2. **租戶服務按需初始化**：
   - 當 LINE webhook 收到訊息時
   - 根據 Channel Token 識別公司
   - 動態載入該公司的 RAG 服務
   - 建立公司專用的工作目錄

---

## ⚙️ 多租戶環境配置

### 核心環境變數

```bash
# PostgreSQL 多租戶資料庫
DATABASE_URL=postgresql://linerag:linerag@localhost:5432/linerag_multitenant

# OpenAI API 配置
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# RAG-Anything 基礎配置
RAG_WORKING_DIR=./rag_storage  # 基礎目錄，各公司會有子目錄
RAG_PARSER=mineru
RAG_PARSE_METHOD=auto

# Redis 配置（會話管理）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 系統管理員設定
ADMIN_LINE_IDS=admin_line_id_1,admin_line_id_2
```

### 公司專用配置

每個公司在資料庫中有專用設定：

- `line_channel_token`：該公司的 LINE Channel Access Token
- `line_channel_secret`：該公司的 LINE Channel Secret
- `rag_working_dir`：該公司的 RAG 工作目錄（如 `./rag_storage/company_1`）
- `subscription_plan`：訂閱方案（影響配額限制）

---

## 🛣️ 多租戶 API 路由設計

### LINE Webhook 多公司路由

```python
@router.post("/webhook")
async def line_webhook(request: Request):
    # 1. 驗證 LINE 簽名
    # 2. 根據 Channel Token 識別公司
    # 3. 取得該公司的 RAG 服務
    # 4. 處理用戶訊息（公司隔離）
```

### 問答 API（多租戶支援）

```python
@router.post("/ask")
async def ask(request: AskRequest, user: User = Depends(get_current_user)):
    # 1. 驗證用戶身份和公司歸屬
    # 2. 取得用戶所屬公司的 RAG 服務
    # 3. 在該公司的知識庫中檢索
    # 4. 記錄審計日誌
```

### 文檔上傳（按公司隔離）

```python
@router.post("/ingest")
async def ingest_document(file: UploadFile, company_id: int):
    # 1. 驗證公司配額
    # 2. 取得該公司的 RAG 服務
    # 3. 在該公司的工作目錄中處理文檔
    # 4. 更新文檔元資料表
```

---

## 🔄 多租戶資料流與處理邏輯

### 1. 公司註冊與初始化流程

```mermaid
graph TD
    A[新公司註冊] --> B[建立 Company 記錄]
    B --> C[設定 LINE Channel 資訊]
    C --> D[建立公司工作目錄]
    D --> E[初始化 RAG 服務實例]
    E --> F[建立管理員帳戶]
    F --> G[公司可開始使用]
```

### 2. 用戶訊息處理流程

```mermaid
graph TD
    A[LINE 用戶傳送訊息] --> B[webhook 接收]
    B --> C[根據 Channel Token 識別公司]
    C --> D[取得/建立用戶記錄]
    D --> E[取得公司 RAG 服務]
    E --> F[在公司知識庫中檢索]
    F --> G[產生回答]
    G --> H[記錄審計日誌]
    H --> I[回傳給用戶]
```

### 3. 文檔處理流程（多租戶）

```mermaid
graph TD
    A[上傳文檔] --> B[驗證公司權限]
    B --> C[檢查配額限制]
    C --> D[取得公司 RAG 服務]
    D --> E[在公司目錄中處理]
    E --> F[向量化並存儲]
    F --> G[更新文檔元資料]
    G --> H[回傳處理結果]
```

---

## 🔐 多租戶安全性與隔離

### 資料隔離策略

1. **資料庫層隔離**：
   - 所有資料表都包含 `company_id` 外鍵
   - 查詢時必須加入公司過濾條件
   - 防止跨公司資料洩露

2. **檔案系統隔離**：

   ```bash
   rag_storage/
   ├── company_1/
   │   ├── documents/
   │   └── vectors/
   ├── company_2/
   │   ├── documents/
   │   └── vectors/
   ```

3. **向量資料庫隔離**：
   - RAG-Anything 按工作目錄分離
   - 每個公司有獨立的向量空間
   - 檢索時自動限制在公司範圍內

### 安全機制

- **API 認證**：每個請求必須攜帶有效的公司和用戶識別
- **權限控制**：admin > cs > user 的三級權限系統
- **配額限制**：按公司設定文檔數量和查詢次數上限
- **審計追蹤**：完整記錄所有操作，支援合規審查

---

## 📊 監控與運維

### 系統監控指標

```python
# 健康檢查包含多租戶狀態
@router.get("/health")
async def health_check():
    return {
        "database": "健康狀態",
        "active_companies": "啟用公司數量",
        "total_users": "總用戶數",
        "rag_services": "載入的 RAG 服務數量",
        "redis_connection": "Redis 連接狀態"
    }
```

### 多租戶統計

- **公司使用統計**：文檔數量、查詢次數、活躍用戶
- **系統資源使用**：記憶體、磁碟空間、API 調用
- **效能監控**：回應時間、錯誤率、並發處理能力

---

## 🚀 部署與擴展

### 多租戶部署架構

```bash
# 1. PostgreSQL 資料庫
docker run --name postgres-multitenant \
  -e POSTGRES_DB=linerag_multitenant \
  -e POSTGRES_USER=linerag \
  -e POSTGRES_PASSWORD=linerag \
  -p 5432:5432 -d postgres:15

# 2. Redis 快取
docker run --name redis-sessions \
  -p 6379:6379 -d redis:alpine

# 3. Qdrant 向量資料庫
docker run --name qdrant-vectors \
  -p 6333:6333 -d qdrant/qdrant

# 4. LineRAG API 應用
docker build -t linerag-multitenant .
docker run -p 8000:8000 linerag-multitenant
```

### 水平擴展策略

- **資料庫分片**：按公司 ID 進行水平分片
- **服務實例**：多個 API 實例負載均衡
- **快取分離**：Redis Cluster 支援更多併發
- **檔案儲存**：遷移到雲端物件儲存（S3、Azure Blob）

---

## 🔧 故障排除

### 常見多租戶問題

1. **公司服務初始化失敗**

   ```bash
   # 檢查公司資料庫記錄
   SELECT * FROM companies WHERE is_active = true;
   
   # 檢查工作目錄權限
   ls -la rag_storage/
   ```

2. **跨公司資料洩露檢查**

   ```sql
   -- 確認所有查詢都包含公司過濾
   SELECT DISTINCT company_id FROM document_metadata;
   ```

3. **效能問題診斷**

   ```bash
   # 檢查載入的 RAG 服務數量
   curl http://localhost:8000/health
   
   # 檢查資料庫連接池
   SELECT * FROM pg_stat_activity;
   ```

---

## 🔮 未來發展規劃

### 短期目標（3個月）

- 完善多公司管理後台
- 實現動態配額調整
- 增加更多審計功能
- 優化多租戶效能

### 中期目標（6個月）

- 支援更多 LINE 以外的渠道
- 實現公司間資料共享機制
- 增加高級分析報表
- 支援白標客製化

### 長期目標（1年）

- 微服務架構拆分
- 支援地理分散部署
- AI 驅動的自動化運維
- 企業級 SLA 保證

---

## 📚 參考資料與相關文檔

- [RAG-Anything 官方文檔](https://github.com/your-org/rag-anything)
- [PostgreSQL 多租戶最佳實踐](https://www.postgresql.org/docs/)
- [FastAPI 企業應用指南](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM 文檔](https://docs.sqlalchemy.org/)

---

**版本**：v2.0 (Multi-Tenant RAG-Anything Framework)
**更新日期**：2025-08-13
**維護者**：羽翔
