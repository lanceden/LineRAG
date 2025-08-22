# PostgreSQL 實體數據庫設置指南

## 1. 安裝 PostgreSQL

### Windows

下載並安裝 PostgreSQL: [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)

### macOS

```bash
brew install postgresql
brew services start postgresql
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## 2. 創建數據庫和用戶

連接到 PostgreSQL:

```bash
sudo -u postgres psql
```

創建數據庫和用戶:

```sql
-- 創建數據庫
CREATE DATABASE linerag;

-- 創建用戶 (可選，也可以使用現有用戶)
CREATE USER linerag_user WITH PASSWORD 'your_secure_password';

-- 授予權限
GRANT ALL PRIVILEGES ON DATABASE linerag TO linerag_user;

-- 退出
\q
```

## 3. 更新連接字串

在 `.env` 文件中設置正確的 DATABASE_URL:

```env
# 使用 postgres 超級用戶
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/linerag

# 或使用專用用戶
DATABASE_URL=postgresql://linerag_user:your_secure_password@localhost:5432/linerag
```

## 4. 初始化數據庫結構

執行數據庫初始化腳本:

```bash
cd apps/api
python init_db.py
```

## 5. 驗證設置

啟動 API 服務並檢查健康狀態:

```bash
curl http://localhost:8000/health
```

應該看到 `"database": "ok"` 的回應。

## 常見問題

### 連接被拒絕

- 確保 PostgreSQL 服務正在運行
- 檢查 `pg_hba.conf` 文件中的認證設置
- 確認防火牆設置允許連接到 5432 端口

### 權限錯誤

- 確保用戶有適當的數據庫權限
- 檢查密碼是否正確

### Docker 容器無法連接外部 PostgreSQL

- 使用 `host.docker.internal` 而不是 `localhost`
- 確保 PostgreSQL 接受外部連接 (修改 `postgresql.conf`)
