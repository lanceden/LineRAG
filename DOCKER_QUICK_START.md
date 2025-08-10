# 🐳 Docker 快速部署指南

## 🚀 統一的啟動方式

### 1. 開發環境

```bash
# 複製開發環境配置
cp .env.development .env

# 啟動開發環境 (使用 OpenAI API)
docker-compose up -d
```

### 2. 生產環境

```bash
# 複製生產環境配置
cp .env.production .env

# 啟動生產環境 (使用 vLLM + GPU)
docker-compose up -d
```

### 3. 快速測試（只啟動必要服務）

```bash
# 只啟動 API 和資料庫，不啟動 vLLM
docker-compose up -d api web qdrant
```

## ⚙️ 環境變數設定

創建 `.env` 文件：

```bash
# 必要的環境變數
OPENAI_API_KEY=your_openai_api_key_here
NEXTAUTH_SECRET=your_nextauth_secret_here

# LINE Bot (可選)
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
LINE_CLIENT_ID=your_line_client_id
LINE_CLIENT_SECRET=your_line_client_secret
```

## 🔧 常用命令

```bash
# 啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f api
docker-compose logs -f web

# 停止所有服務
docker-compose down

# 重新建置並啟動
docker-compose up --build -d

# 清理所有資料 (危險！)
docker-compose down -v
```

## 📋 服務訪問

| 服務         | URL                                     | 說明         |
| ------------ | --------------------------------------- | ------------ |
| Web 前端     | <http://localhost:3000>                 | Next.js 應用 |
| API 後端     | <http://localhost:8000>                 | FastAPI 文檔 |
| API 健康檢查 | <http://localhost:8000/health>          | 系統狀態     |
| API 文檔     | <http://localhost:8000/docs>            | Swagger UI   |
| 任務狀態     | <http://localhost:8000/tasks/{task_id}> | 異步任務查詢 |
| vLLM         | <http://localhost:8001>                 | 模型推理     |
| Qdrant       | <http://localhost:6333>                 | 向量資料庫   |
| Redis        | localhost:6379                          | 任務隊列     |

## 🛠️ 故障排除

### 1. 檢查容器狀態

```bash
docker-compose ps
```

### 2. 檢查日誌

```bash
docker-compose logs api
```

### 3. 重新啟動特定服務

```bash
docker-compose restart api
```

### 4. 進入容器調試

```bash
docker-compose exec api bash
```

### 5. 檢查健康狀態

```bash
curl http://localhost:8000/health
```

## 🔄 完全重新安裝

### 當遇到build錯誤或服務異常時，完全重置Docker環境

#### 步驟1：停止並清理所有服務

```bash
# 停止所有容器並移除volumes（⚠️ 會刪除所有資料）
docker-compose down -v --remove-orphans
```

#### 步驟2：清理Docker系統（可選）

```bash
# 清理所有未使用的映像和建置快取
docker system prune -a
docker builder prune -a
```

#### 步驟3：重新建置所有服務

```bash
# 無快取重新建置所有映像
docker-compose build --no-cache
```

#### 步驟4：重新啟動

```bash
# 背景啟動所有服務
docker-compose up -d
```

#### 步驟5：驗證服務

```bash
# 檢查服務狀態
docker-compose ps

# 查看即時日誌
docker-compose logs -f

# 檢查特定服務
docker-compose logs api
docker-compose logs web
```

### ⚠️ 重要提醒

**資料遺失警告：**

- `docker-compose down -v` 會刪除所有volumes
- 包括：向量資料庫、Redis資料、上傳的檔案、模型快取
- 執行前請確保重要資料已備份

**時間成本：**

- 完全重建需要20-30分鐘
- vLLM映像較大，下載時間較長
- 模型會重新下載

**建議順序：**

1. 先嘗試重啟特定服務：`docker-compose restart <service>`
2. 再試重建特定服務：`docker-compose build --no-cache <service>`
3. 最後才完全重置系統

## 💡 開發技巧

### 開發模式建議

#### 方案1：本地開發 + Docker服務

```bash
# 只啟動後端服務 (vLLM, Qdrant, Redis)
docker-compose up -d vllm qdrant redis

# 安裝 FastAPI 依賴
cd apps/api
pip install -r requirements.txt

# 本地運行 FastAPI (支援熱重載)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 另開終端，安裝 Next.js 依賴
cd apps/web
npm install

# 本地運行 Next.js (支援熱重載)
npm run dev
```

#### 方案2：重建服務熱更新

```bash
# 修改程式後，重建並重啟特定服務
docker-compose up -d --build api  # 重建API服務
docker-compose up -d --build web  # 重建Web服務
```

**💡 推薦方案1** - 保持環境一致性，只有應用層本地運行

### 只啟動需要的服務

```bash
# 只啟動 API 
docker-compose up -d api

# 只啟動 Web
docker-compose up -d web
```

### 資料持久化

所有重要資料都存在 Docker volumes 中：

- `api_data`: 向量資料庫資料
- `api_uploads`: 上傳的檔案
- `model_cache`: 下載的模型

## 🤖 模型配置

### vLLM 模型切換

編輯 `docker-compose.yml` 中的 vLLM 服務配置：

```yaml
# 開發/測試環境 (輕量模型)
command: >
  --model facebook/opt-1.3b
  --served-model-name opt-1.3b
  --max-model-len 2048
  --gpu-memory-utilization 0.6

# 正式環境 (大模型，更好效果)
command: >
  --model Qwen/Qwen2.5-7B-Instruct
  --served-model-name Qwen2.5-7B-Chat
  --max-model-len 4096
  --gpu-memory-utilization 0.8
```

### 常用模型清單

| 模型名稱                    | 大小 | 適用場景 | GPU記憶體需求 |
| --------------------------- | ---- | -------- | ------------- |
| `facebook/opt-1.3b`         | 1.3B | 開發測試 | ~3GB          |
| `microsoft/DialoGPT-medium` | 774M | 輕量對話 | ~2GB          |
| `Qwen/Qwen2.5-7B-Instruct`  | 7B   | 正式生產 | ~14GB         |
| `microsoft/DialoGPT-large`  | 1.5B | 英文對話 | ~4GB          |

### 環境變數對應

更換模型後，同時更新 `.env` 文件：

```bash
# 在 .env.development 或 .env.production 中
LLM_MODEL_NAME=opt-1.3b  # 要與 served-model-name 一致
```

### 模型更換步驟

```bash
# 1. 修改 docker-compose.yml 中的模型配置
# 2. 更新環境變數
# 3. 重啟 vLLM 服務
docker-compose restart vllm

# 4. 查看載入進度
docker-compose logs -f vllm

# 5. 測試模型
curl http://localhost:8001/v1/models
```

### 模型載入時間

- **小模型 (1-2B)**：1-2分鐘
- **中模型 (3-7B)**：3-5分鐘  
- **大模型 (7B+)**：5-10分鐘

**💡 提示：** 首次載入會下載模型檔案，後續啟動會使用快取，速度較快。

## 🔒 安全性設定

### 生產環境

1. 更改 `NEXTAUTH_SECRET`
2. 使用強密碼
3. 配置 HTTPS
4. 限制網路訪問

### 環境變數檔案

創建不同環境的 `.env` 文件：

- `.env.development`
- `.env.production`
- `.env.staging`

## 📊 監控與日誌

### 查看即時日誌

```bash
docker-compose logs -f --tail=100
```

### 資源使用情況

```bash
docker stats
```

### 清理系統

```bash
# 清理未使用的容器和映像
docker system prune -a
```

## 🚦 常見問題

**Q: 端口已被佔用？**

```bash
# 更改 docker-compose.yml 中的端口映射
ports:
  - "3001:3000"  # 改為 3001
```

**Q: 記憶體不足？**

```bash
# 調整 vLLM 設定
command: >
  --model TheBloke/Qwen2-7B-Chat-AWQ
  --max-model-len 2048
  --gpu-memory-utilization 0.6
```

**Q: 模型下載慢？**

```bash
# 預先下載模型到本地
docker-compose exec vllm bash
huggingface-cli download TheBloke/Qwen2-7B-Chat-AWQ
```

---

最推薦從開發模式開始：`docker-compose -f docker-compose.dev.yml up -d` 🎉
