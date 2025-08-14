# 生產環境部署指南

## 🚀 Nginx 反向代理部署

### 1. 安裝 Nginx

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx

# macOS
brew install nginx
```

### 2. 配置 Nginx

```bash
# 複製配置檔案
sudo cp nginx.conf.example /etc/nginx/sites-available/linerag

# 啟用站點
sudo ln -s /etc/nginx/sites-available/linerag /etc/nginx/sites-enabled/

# 測試配置
sudo nginx -t

# 重新載入 Nginx
sudo systemctl reload nginx
```

### 3. 更新環境變數

修改 `.env` 檔案：

```env
# 生產環境 API 端點
NEXT_PUBLIC_PYTHON_API_URL=https://your-domain.com/api
PYTHON_API_URL=http://127.0.0.1:8000/api

# NextAuth 設定
NEXTAUTH_URL=https://your-domain.com
NEXTAUTH_SECRET=your-production-secret-key
```

### 4. 啟動服務

```bash
# 啟動 Docker 服務
docker-compose up -d

# 檢查服務狀態
docker-compose ps
```

## 🔧 API 前綴配置

### 當前配置

- **前端**: `http://your-domain.com/`
- **API**: `http://your-domain.com/api/`
- **API 文檔**: `http://your-domain.com/api/docs`
- **健康檢查**: `http://your-domain.com/api/health`

### 路由結構

```text
/                    → Next.js 前端
/api/health          → 健康檢查
/api/docs           → API 文檔
/api/ask            → RAG 問答
/api/ingest         → 文檔上傳
/api/webhook/line   → LINE Bot Webhook
/api/users          → 用戶管理
/api/admin          → 管理功能
```

## 🛡️ 安全配置

### 1. SSL/TLS (推薦)

```bash
# 使用 Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

### 2. 防火牆設定

```bash
# 只開放必要端口
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### 3. 環境變數保護

```bash
# 設定適當權限
chmod 600 .env
chown root:root .env
```

## 📊 監控和日誌

### 1. Nginx 日誌

```bash
# 檢視訪問日誌
sudo tail -f /var/log/nginx/linerag.access.log

# 檢視錯誤日誌
sudo tail -f /var/log/nginx/linerag.error.log
```

### 2. Docker 日誌

```bash
# API 服務日誌
docker-compose logs -f api

# 前端服務日誌
docker-compose logs -f web

# 所有服務日誌
docker-compose logs -f
```

### 3. 健康檢查

```bash
# 檢查 API 健康狀態
curl https://your-domain.com/api/health

# 檢查前端狀態
curl https://your-domain.com
```

## 🔄 更新部署

### 1. 更新程式碼

```bash
# 拉取最新程式碼
git pull origin main

# 重建並重啟服務
docker-compose build
docker-compose up -d
```

### 2. 資料庫遷移

```bash
# 執行資料庫遷移
cd apps/api
python db_manager.py
# 選擇選項 3: 升級資料庫
```

### 3. 清理舊映像

```bash
# 清理未使用的 Docker 映像
docker system prune -f
```

## 🚨 故障排除

### 1. 502 Bad Gateway

```bash
# 檢查後端服務是否運行
docker-compose ps
curl http://localhost:8000/api/health
```

### 2. 404 Not Found

```bash
# 檢查 Nginx 配置
sudo nginx -t
sudo systemctl status nginx
```

### 3. CORS 錯誤

檢查 `main.py` 中的 CORS 設定：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 更新為正確的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📋 檢查清單

部署前確認：

- [ ] 資料庫已設定並可連接
- [ ] OpenAI API Key 已設定
- [ ] Nginx 配置已更新域名
- [ ] SSL 證書已安裝（生產環境）
- [ ] 防火牆規則已設定
- [ ] 環境變數權限已設定
- [ ] 健康檢查通過
- [ ] 日誌輪轉已設定

---

完成這些步驟後，你的 LineRAG 系統就可以在生產環境中運行了！
