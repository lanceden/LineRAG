# FastAPI 部署指南

## 本地開發環境

### 1. 安裝依賴

```bash
cd apps/api
pip install -r requirements.txt
```

### 2. 環境變數設定

創建 `.env` 檔案：

```bash
# OpenAI / vLLM 設定
OPENAI_API_BASE=http://localhost:8001/v1
OPENAI_API_KEY=not-needed
LLM_MODEL_NAME=TheBloke/Qwen2-7B-Chat-AWQ

# 向量資料庫設定
EMBEDDING_MODEL_NAME=BAAI/bge-m3
USE_LOCAL_QDRANT=true
QDRANT_PATH=./local_qdrant
COLLECTION_NAME=documents

# LINE Bot 設定（可選）
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# 檔案上傳設定
UPLOAD_IMAGE_DIR=./uploads/images
```

### 3. 啟動開發伺服器

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 生產環境部署

### 方案 1: Docker 部署

#### 1. 創建 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 創建上傳目錄
RUN mkdir -p uploads/images local_qdrant

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 創建 docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_BASE=http://vllm:8000/v1
      - USE_LOCAL_QDRANT=true
      - QDRANT_PATH=/app/data/qdrant
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    depends_on:
      - vllm

  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8001:8000"
    command: >
      --model TheBloke/Qwen2-7B-Chat-AWQ
      --served-model-name Qwen2-7B-Chat
      --host 0.0.0.0
      --port 8000
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    environment:
      - CUDA_VISIBLE_DEVICES=0
```

#### 3. 部署命令

```bash
docker-compose up -d
```

### 方案 2: 雲端平台部署

#### Railway

1. 連接 GitHub 倉庫到 Railway
2. 設定環境變數
3. Railway 會自動偵測並部署 FastAPI 應用

#### Render

1. 創建 `render.yaml`：

```yaml
services:
  - type: web
    name: linerag-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.0
      - key: USE_LOCAL_QDRANT
        value: true
```

#### Google Cloud Run

1. 創建 Dockerfile（同上）
2. 建置並推送映像：

```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/linerag-api
```

3. 部署到 Cloud Run：

```bash
gcloud run deploy --image gcr.io/PROJECT-ID/linerag-api --platform managed
```

### 方案 3: VPS 部署

#### 1. 伺服器設定

```bash
# 安裝 Python 和依賴
sudo apt update
sudo apt install python3 python3-pip nginx supervisor

# 創建應用目錄
sudo mkdir -p /var/www/linerag-api
cd /var/www/linerag-api

# 複製代碼並安裝依賴
git clone YOUR_REPO .
pip3 install -r requirements.txt
```

#### 2. Supervisor 設定

創建 `/etc/supervisor/conf.d/linerag-api.conf`：

```ini
[program:linerag-api]
command=/usr/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
directory=/var/www/linerag-api
autostart=true
autorestart=true
stderr_logfile=/var/log/linerag-api.err.log
stdout_logfile=/var/log/linerag-api.out.log
user=www-data
```

#### 3. Nginx 設定

創建 `/etc/nginx/sites-available/linerag-api`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 檔案上傳大小限制
    client_max_body_size 10M;
}
```

#### 4. 啟動服務

```bash
# 啟用 Nginx 站點
sudo ln -s /etc/nginx/sites-available/linerag-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 啟動 Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start linerag-api
```

## 效能最佳化

### 1. 使用 Gunicorn

```bash
pip install gunicorn

# 啟動命令
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 2. 快取設定

```python
# 在 main.py 中添加
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
```

## 監控與日誌

### 1. 健康檢查

API 已包含健康檢查端點：`GET /health`

### 2. 日誌設定

```python
# 在 app/core/logging.py 中設定
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
```

## 安全性考量

### 1. 環境變數

- 使用 `.env` 檔案管理敏感資訊
- 生產環境中使用環境變數而非檔案

### 2. HTTPS

```bash
# 使用 Certbot 獲取 SSL 證書
sudo certbot --nginx -d your-domain.com
```

### 3. CORS 設定

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 故障排除

### 常見問題

1. **依賴安裝失敗**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

2. **Qdrant 連接失敗**
   - 檢查 `USE_LOCAL_QDRANT` 環境變數
   - 確認 Qdrant 服務正在運行

3. **記憶體不足**
   - 使用較小的 AI 模型
   - 增加系統 swap 空間

4. **埠口衝突**
   - 檢查埠口 8000 是否被占用
   - 使用 `--port` 參數指定不同埠口
  