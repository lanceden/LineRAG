# LineRAG 多租戶 AI 智能客服系統 - API 文檔

## 📋 文檔資訊

- **版本**: 2.0.0
- **更新日期**: 2025-01-27
- **API 基礎路徑**: `/api`
- **認證方式**: JWT Bearer Token
- **內容格式**: JSON

---

## 🔐 認證機制

### JWT Token 格式

所有需要認證的 API 請求都必須在 Header 中包含 JWT Token：

```http
Authorization: Bearer <jwt_token>
```

### Token 結構
```json
{
  "user_id": 123,
  "company_id": 1,
  "role": "admin",
  "permissions": ["read", "write", "manage"],
  "exp": 1640995200
}
```

### 取得 Token
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@company.com",
  "password": "password123"
}
```

**回應:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 123,
    "email": "admin@company.com",
    "role": "admin",
    "company_id": 1
  }
}
```

---

## 🏥 健康檢查 API

### 系統健康狀態

```http
GET /api/health
```

**回應:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00Z",
  "version": "2.0.0",
  "services": {
    "database": "healthy",
    "qdrant": "healthy",
    "rag_service": "healthy"
  },
  "uptime": "72h30m15s"
}
```

---

## 🤖 智能問答 API

### 文字問答

處理純文字問答請求，使用 RAG 檢索相關內容並生成回應。

```http
POST /api/ask
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**請求參數:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "請問你們的營業時間是什麼時候？"
    }
  ],
  "company_id": 1,
  "stream": true
}
```

**回應 (串流):**
```
data: {"type": "text", "text": "根據我們的資料，營業時間是週一到週五上午9點到下午6點"}

data: [DONE]
```

**錯誤回應:**
```json
{
  "error": "service_unavailable",
  "message": "RAG service not initialized",
  "code": 503
}
```

### 多模態問答

處理包含圖像、文檔等多模態內容的問答請求。

```http
POST /api/ask/multimodal
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**請求參數:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "這張圖片中的產品規格是什麼？"
    }
  ],
  "multimodal_content": {
    "images": [
      {
        "url": "https://example.com/product.jpg",
        "description": "產品規格圖"
      }
    ]
  },
  "company_id": 1,
  "stream": true
}
```

---

## 📄 文檔管理 API

### 上傳文檔

支援多種格式的文檔上傳，包括 PDF、Office 文件、圖像等。

```http
POST /api/documents/upload
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
```

**請求參數:**
```
file: <binary_file>
company_id: 1
category: "產品手冊"
description: "2025年產品規格說明"
```

**回應:**
```json
{
  "task_id": "doc_123456789",
  "status": "processing",
  "message": "文檔上傳成功，正在處理中",
  "document": {
    "id": "doc_123456789",
    "filename": "product_manual.pdf",
    "size": 2048576,
    "type": "application/pdf",
    "company_id": 1,
    "category": "產品手冊",
    "uploaded_at": "2025-01-27T10:30:00Z"
  }
}
```

### 查詢文檔列表

```http
GET /api/documents?company_id=1&page=1&limit=20&category=產品手冊
Authorization: Bearer <jwt_token>
```

**回應:**
```json
{
  "documents": [
    {
      "id": "doc_123456789",
      "filename": "product_manual.pdf",
      "size": 2048576,
      "type": "application/pdf",
      "category": "產品手冊",
      "status": "processed",
      "uploaded_at": "2025-01-27T10:30:00Z",
      "processed_at": "2025-01-27T10:35:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  }
}
```

### 刪除文檔

```http
DELETE /api/documents/{document_id}
Authorization: Bearer <jwt_token>
```

**回應:**
```json
{
  "message": "文檔刪除成功",
  "document_id": "doc_123456789"
}
```

### 文檔處理狀態

```http
GET /api/documents/{document_id}/status
Authorization: Bearer <jwt_token>
```

**回應:**
```json
{
  "document_id": "doc_123456789",
  "status": "processed",
  "progress": 100,
  "processing_steps": [
    {
      "step": "upload",
      "status": "completed",
      "timestamp": "2025-01-27T10:30:00Z"
    },
    {
      "step": "parsing",
      "status": "completed",
      "timestamp": "2025-01-27T10:32:00Z"
    },
    {
      "step": "vectorization",
      "status": "completed",
      "timestamp": "2025-01-27T10:35:00Z"
    }
  ]
}
```

---

## 🏢 公司管理 API

### 建立公司

```http
POST /api/companies
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**請求參數:**
```json
{
  "name": "ABC 科技公司",
  "code": "ABC_TECH",
  "line_channel_token": "your_line_channel_token",
  "line_channel_secret": "your_line_channel_secret",
  "subscription_plan": "premium",
  "max_documents": 5000,
  "max_queries_per_month": 50000,
  "storage_quota_gb": 50
}
```

**回應:**
```json
{
  "id": 2,
  "name": "ABC 科技公司",
  "code": "ABC_TECH",
  "line_bot_enabled": true,
  "subscription_plan": "premium",
  "rag_working_dir": "./rag_storage/company_2",
  "created_at": "2025-01-27T10:30:00Z",
  "is_active": true
}
```

### 更新公司設定

```http
PUT /api/companies/{company_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**請求參數:**
```json
{
  "line_channel_token": "new_line_channel_token",
  "max_documents": 10000,
  "storage_quota_gb": 100
}
```

### 取得公司資訊

```http
GET /api/companies/{company_id}
Authorization: Bearer <jwt_token>
```

**回應:**
```json
{
  "id": 1,
  "name": "XYZ 企業",
  "code": "XYZ_CORP",
  "line_bot_enabled": true,
  "subscription_plan": "standard",
  "max_documents": 1000,
  "max_queries_per_month": 10000,
  "storage_quota_gb": 10,
  "current_documents": 245,
  "current_queries_this_month": 3420,
  "storage_used_gb": 2.5,
  "created_at": "2025-01-01T00:00:00Z",
  "is_active": true
}
```

### 公司列表

```http
GET /api/companies?page=1&limit=10&active=true
Authorization: Bearer <jwt_token>
```

**回應:**
```json
{
  "companies": [
    {
      "id": 1,
      "name": "XYZ 企業",
      "code": "XYZ_CORP",
      "subscription_plan": "standard",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 5,
    "pages": 1
  }
}
```

---

## 👥 用戶管理 API

### 系統用戶管理

#### 建立系統用戶

```http
POST /api/system-users
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**請求參數:**
```json
{
  "email": "admin@newcompany.com",
  "password": "secure_password123",
  "name": "張管理員",
  "role": "company_admin",
  "accessible_companies": [1, 2]
}
```

**回應:**
```json
{
  "id": 10,
  "email": "admin@newcompany.com",
  "name": "張管理員",
  "role": "company_admin",
  "accessible_companies": [1, 2],
  "is_active": true,
  "created_at": "2025-01-27T10:30:00Z"
}
```

#### 系統用戶列表

```http
GET /api/system-users?page=1&limit=20&role=company_admin
Authorization: Bearer <jwt_token>
```

### 租戶用戶管理

#### 建立租戶用戶

```http
POST /api/tenant-users
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**請求參數:**
```json
{
  "company_id": 1,
  "line_id": "U1234567890abcdef",
  "name": "王小明",
  "email": "wang@company.com",
  "role": "user"
}
```

#### 租戶用戶列表

```http
GET /api/tenant-users?company_id=1&page=1&limit=20
Authorization: Bearer <jwt_token>
```

**回應:**
```json
{
  "users": [
    {
      "id": 100,
      "company_id": 1,
      "line_id": "U1234567890abcdef",
      "name": "王小明",
      "email": "wang@company.com",
      "role": "user",
      "last_active": "2025-01-27T09:15:00Z",
      "created_at": "2025-01-20T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

---

## 🔗 LINE Webhook API

### LINE 訊息處理

LINE 平台會向此端點發送用戶訊息事件。

```http
POST /api/webhook
Content-Type: application/json
X-Line-Signature: <line_signature>
```

**請求參數 (LINE 格式):**
```json
{
  "events": [
    {
      "type": "message",
      "message": {
        "type": "text",
        "text": "請問營業時間？"
      },
      "source": {
        "userId": "U1234567890abcdef",
        "type": "user"
      },
      "replyToken": "reply_token_123",
      "timestamp": 1640995200000
    }
  ]
}
```

**回應:**
```
ok
```

**處理流程:**
1. 驗證 LINE 簽名
2. 根據 Channel Token 識別公司
3. 取得或建立用戶資料
4. 使用公司的 RAG 服務生成回應
5. 透過 LINE API 回覆訊息
6. 記錄審計日誌

---

## 📊 管理後台 API

### 統計資料

#### 系統概覽

```http
GET /api/admin/dashboard
Authorization: Bearer <jwt_token>
```

**回應:**
```json
{
  "overview": {
    "total_companies": 5,
    "active_companies": 4,
    "total_documents": 1250,
    "total_queries_today": 420,
    "total_users": 850
  },
  "recent_activity": [
    {
      "timestamp": "2025-01-27T10:25:00Z",
      "company": "XYZ 企業",
      "action": "document_uploaded",
      "details": "上傳產品手冊.pdf"
    }
  ],
  "system_health": {
    "api_response_time": "120ms",
    "database_status": "healthy",
    "rag_service_status": "healthy",
    "storage_usage": "65%"
  }
}
```

#### 公司使用統計

```http
GET /api/admin/companies/{company_id}/stats?period=30d
Authorization: Bearer <jwt_token>
```

**回應:**
```json
{
  "company_id": 1,
  "period": "30d",
  "stats": {
    "total_queries": 8500,
    "successful_queries": 8100,
    "success_rate": 95.3,
    "avg_response_time": "1.2s",
    "documents_processed": 45,
    "storage_used": "2.5GB",
    "active_users": 120
  },
  "daily_breakdown": [
    {
      "date": "2025-01-27",
      "queries": 280,
      "success_rate": 96.1
    }
  ]
}
```

### 審計日誌

```http
GET /api/admin/audit-logs?company_id=1&action=document_uploaded&page=1&limit=50
Authorization: Bearer <jwt_token>
```

**回應:**
```json
{
  "logs": [
    {
      "id": 12345,
      "company_id": 1,
      "user_id": 100,
      "action": "document_uploaded",
      "resource_type": "document",
      "resource_id": "doc_123456789",
      "status": "success",
      "timestamp": "2025-01-27T10:30:00Z",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0..."
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1250,
    "pages": 25
  }
}
```

---

## 🔧 系統配置 API

### 環境變數配置

```http
GET /api/admin/config
Authorization: Bearer <jwt_token>
```

**回應:**
```json
{
  "rag_config": {
    "max_document_size": "50MB",
    "supported_formats": ["pdf", "docx", "txt", "jpg", "png"],
    "vector_dimension": 1536,
    "retrieval_top_k": 5
  },
  "gpt_config": {
    "model": "gpt-4",
    "max_tokens": 2000,
    "temperature": 0.7
  },
  "system_limits": {
    "max_companies": 100,
    "max_documents_per_company": 10000,
    "max_queries_per_minute": 60
  }
}
```

### 更新系統配置

```http
PUT /api/admin/config
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**請求參數:**
```json
{
  "gpt_config": {
    "temperature": 0.8,
    "max_tokens": 2500
  },
  "system_limits": {
    "max_queries_per_minute": 100
  }
}
```

---

## ❌ 錯誤碼定義

### HTTP 狀態碼

| 狀態碼 | 說明 | 常見原因 |
|--------|------|----------|
| 200 | 成功 | 請求處理成功 |
| 201 | 建立成功 | 資源建立成功 |
| 400 | 請求錯誤 | 參數格式錯誤、必填欄位缺失 |
| 401 | 未授權 | Token 無效或過期 |
| 403 | 禁止存取 | 權限不足 |
| 404 | 找不到資源 | 資源不存在 |
| 409 | 衝突 | 資源已存在、狀態衝突 |
| 422 | 無法處理 | 資料驗證失敗 |
| 429 | 請求過多 | 超過速率限制 |
| 500 | 伺服器錯誤 | 內部系統錯誤 |
| 503 | 服務不可用 | 服務暫時無法使用 |

### 自定義錯誤碼

```json
{
  "error": "invalid_company_id",
  "message": "指定的公司 ID 不存在或無權存取",
  "code": 404,
  "details": {
    "company_id": 999,
    "user_accessible_companies": [1, 2, 3]
  }
}
```

#### 常見錯誤碼

| 錯誤碼 | HTTP 狀態 | 說明 |
|--------|-----------|------|
| `invalid_token` | 401 | JWT Token 無效 |
| `token_expired` | 401 | JWT Token 已過期 |
| `insufficient_permissions` | 403 | 權限不足 |
| `company_not_found` | 404 | 公司不存在 |
| `document_not_found` | 404 | 文檔不存在 |
| `user_not_found` | 404 | 用戶不存在 |
| `company_code_exists` | 409 | 公司代碼已存在 |
| `email_exists` | 409 | 電子郵件已存在 |
| `file_too_large` | 422 | 檔案大小超過限制 |
| `unsupported_file_type` | 422 | 不支援的檔案格式 |
| `quota_exceeded` | 422 | 超過配額限制 |
| `rate_limit_exceeded` | 429 | 超過請求頻率限制 |
| `rag_service_unavailable` | 503 | RAG 服務不可用 |
| `database_connection_error` | 503 | 資料庫連接錯誤 |

---

## 📝 請求/回應範例

### 完整的文檔上傳流程

#### 1. 上傳文檔
```bash
curl -X POST "https://api.linerag.com/api/documents/upload" \
  -H "Authorization: Bearer your_jwt_token" \
  -F "file=@product_manual.pdf" \
  -F "company_id=1" \
  -F "category=產品手冊" \
  -F "description=2025年產品規格說明"
```

#### 2. 檢查處理狀態
```bash
curl -X GET "https://api.linerag.com/api/documents/doc_123456789/status" \
  -H "Authorization: Bearer your_jwt_token"
```

#### 3. 測試問答
```bash
curl -X POST "https://api.linerag.com/api/ask" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "這個產品的保固期是多久？"
      }
    ],
    "company_id": 1,
    "stream": false
  }'
```

### 完整的公司設定流程

#### 1. 建立公司
```bash
curl -X POST "https://api.linerag.com/api/companies" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新科技公司",
    "code": "NEW_TECH",
    "line_channel_token": "your_line_channel_token",
    "line_channel_secret": "your_line_channel_secret"
  }'
```

#### 2. 建立公司管理員
```bash
curl -X POST "https://api.linerag.com/api/system-users" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@newtech.com",
    "password": "secure_password123",
    "name": "新科技管理員",
    "role": "company_admin",
    "accessible_companies": [2]
  }'
```

#### 3. 設定 LINE Webhook
在 LINE Developers Console 中設定 Webhook URL：
```
https://api.linerag.com/api/webhook
```

---

## 🔄 API 版本控制

### 版本策略

- **當前版本**: v2.0
- **支援版本**: v2.x
- **棄用版本**: v1.x (2025-12-31 停止支援)

### 版本指定

可透過 Header 指定 API 版本：
```http
Accept: application/vnd.linerag.v2+json
```

或透過 URL 路徑：
```http
GET /api/v2/companies
```

### 版本變更記錄

#### v2.0.0 (2025-01-27)
- 新增多租戶架構支援
- 新增多模態問答 API
- 改進文檔處理流程
- 新增審計日誌功能

#### v1.2.0 (2024-12-15)
- 新增 LINE Webhook 支援
- 改進錯誤處理機制
- 新增檔案上傳進度追蹤

---

## 🚀 效能指標

### API 回應時間基準

| API 端點 | 平均回應時間 | 95% 百分位 |
|----------|-------------|-----------|
| `/health` | 10ms | 20ms |
| `/ask` | 1.2s | 3.0s |
| `/documents/upload` | 500ms | 1.5s |
| `/companies` | 50ms | 150ms |
| `/webhook` | 200ms | 500ms |

### 速率限制

| 用戶類型 | 每分鐘請求數 | 每日請求數 |
|----------|-------------|-----------|
| 系統管理員 | 1000 | 50000 |
| 公司管理員 | 500 | 20000 |
| 一般用戶 | 100 | 5000 |
| LINE Webhook | 無限制 | 無限制 |

---

## 🧪 測試環境

### 測試 API 基礎路徑
```
https://api-test.linerag.com/api
```

### 測試用戶帳號
```json
{
  "email": "test@linerag.com",
  "password": "test123456",
  "role": "system_admin"
}
```

### 測試公司資料
```json
{
  "company_id": 999,
  "name": "測試公司",
  "code": "TEST_COMPANY"
}
```

---

## 📞 API 支援

### 技術支援管道

- **API 文檔問題**: api-docs@linerag.com
- **整合技術支援**: integration@linerag.com
- **錯誤回報**: bugs@linerag.com
- **功能建議**: features@linerag.com

### 開發者社群

- **Discord**: https://discord.gg/linerag
- **GitHub Issues**: https://github.com/linerag/api/issues
- **Stack Overflow**: 標籤 `linerag-api`

---

*本 API 文檔版權所有 © 2025 LineRAG 開發團隊*