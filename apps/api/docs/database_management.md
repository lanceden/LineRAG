# Python 資料庫管理指南

## 📋 概述

本指南說明如何在 Python 專案中進行資料庫管理，包含 Schema 設計、遷移管理、和維護操作。

## 🛠️ 工具選擇

### Python 資料庫管理工具比較

| 工具                     | 類似工具            | 特點                 | 適用場景    |
| ------------------------ | ------------------- | -------------------- | ----------- |
| **Alembic + SQLAlchemy** | Prisma, EF          | 功能完整、生態成熟   | 大型專案 ✅  |
| **Django ORM**           | Rails Active Record | 整合度高、遷移自動化 | Django 專案 |
| **Tortoise ORM**         | Prisma              | 異步支援、現代語法   | 異步應用    |
| **Peewee**               | -                   | 輕量級、簡單易用     | 小型專案    |

### 本專案選擇：Alembic + SQLAlchemy

**優點：**

- 🎯 最接近 Prisma 和 EF 的體驗
- 📦 生態系統完整
- 🔄 遷移版本控制
- 🏗️ Schema 自動生成
- 🔍 資料庫檢查和驗證

## 🚀 快速開始

### 1. 安裝依賴

已包含在 `requirements.txt` 中：

```txt
sqlalchemy
alembic
psycopg2-binary
```

### 2. 初始化 Alembic（僅第一次）

```bash
cd apps/api
alembic init alembic
```

### 3. 配置 Alembic

編輯 `alembic/env.py`：

```python
from app.core.database import Base
from app.models import *  # 導入所有模型

target_metadata = Base.metadata
```

編輯 `alembic.ini`：

```ini
sqlalchemy.url = postgresql://linerag:your_password@localhost:5432/lineragdb
```

## 📊 資料庫 Schema 管理

### 當前資料表結構

```text
lineragdb/
├── companies          # 公司資料表
│   ├── id (PK)
│   ├── name
│   ├── code (unique)
│   ├── line_channel_token
│   ├── line_channel_secret
│   ├── subscription_plan
│   ├── max_documents
│   ├── max_queries_per_month
│   └── rag_working_dir
│
├── users              # 用戶資料表
│   ├── id (PK)
│   ├── company_id (FK → companies.id)
│   ├── line_id
│   ├── name
│   ├── role
│   └── created_at
│
└── document_metadata  # 文檔元資料
    ├── id (PK)
    ├── company_id (FK → companies.id)
    ├── filename
    ├── file_path
    ├── upload_time
    └── status
```

### Model 定義位置

- `app/models/company.py` - 公司模型
- `app/models/user.py` - 用戶模型
- `app/models/document.py` - 文檔模型

## 🔄 遷移管理

### 創建新遷移

```bash
# 自動檢測模型變更並生成遷移
alembic revision --autogenerate -m "描述變更內容"

# 手動創建空的遷移文件
alembic revision -m "手動遷移"
```

### 執行遷移

```bash
# 升級到最新版本
alembic upgrade head

# 升級到特定版本
alembic upgrade [revision_id]

# 降級到上一版本
alembic downgrade -1

# 降級到特定版本
alembic downgrade [revision_id]
```

### 查看遷移狀態

```bash
# 查看當前版本
alembic current

# 查看遷移歷史
alembic history

# 查看待執行的遷移
alembic show head
```

## 🏗️ 資料庫初始化

### 使用 init_db.py

```bash
cd apps/api
python init_db.py
```

**功能：**

- ✅ 創建所有資料表
- ✅ 建立示範公司資料
- ✅ 創建系統管理員帳戶
- ✅ 設置初始權限

### 手動初始化步驟

```python
# 1. 創建資料表
from app.core.database import create_tables
create_tables()

# 2. 創建公司
from app.models.company import Company
company = Company(
    name="你的公司",
    code="YOUR_COMPANY", 
    subscription_plan="standard"
)

# 3. 創建管理員
from app.models.system_user import SystemUser
admin = SystemUser(
    username="admin",
    email="admin@company.com",
    password_hash="hashed_password",
    full_name="系統管理員",
    role="super_admin"
)
```

## 🔧 維護操作

### 備份資料庫

```bash
# PostgreSQL 備份
pg_dump -h localhost -U linerag lineragdb > backup_$(date +%Y%m%d).sql

# 還原備份
psql -h localhost -U linerag lineragdb < backup_20250813.sql
```

### 資料庫清理

```bash
# 清理舊的文檔記錄
python -c "
from app.core.database import SessionLocal
from app.models.document import DocumentMetadata
from datetime import datetime, timedelta

db = SessionLocal()
old_docs = db.query(DocumentMetadata).filter(
    DocumentMetadata.upload_time < datetime.now() - timedelta(days=90)
).all()
for doc in old_docs:
    db.delete(doc)
db.commit()
"
```

### 效能監控

```python
# 查看資料表大小
from sqlalchemy import text
from app.core.database import SessionLocal

db = SessionLocal()
result = db.execute(text("""
    SELECT 
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
    FROM pg_tables 
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"""))

for row in result:
    print(f"{row.tablename}: {row.size}")
```

## 🚨 故障排除

### 常見問題

#### 1. 遷移衝突

```bash
# 查看衝突的遷移
alembic history

# 手動解決衝突後標記為已執行
alembic stamp head
```

#### 2. 資料表已存在錯誤

```bash
# 標記當前狀態為初始遷移
alembic stamp base
alembic upgrade head
```

#### 3. 連接錯誤

```bash
# 檢查 PostgreSQL 服務狀態
sudo systemctl status postgresql

# 測試連接
psql -h localhost -U linerag -d lineragdb -c "SELECT version();"
```

### 除錯模式

```python
# 啟用 SQLAlchemy 日誌
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## 📝 最佳實踐

### 1. 遷移檔案命名

```text
20250813_001_add_user_table.py
20250813_002_add_company_foreign_key.py
20250814_001_create_document_index.py
```

### 2. 模型設計原則

```python
class BaseModel(Base):
    """所有模型的基礎類別"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 3. 多租戶設計

- 每個資料表包含 `company_id` 外鍵
- 所有查詢都要包含公司篩選條件
- 使用 RAG 資料夾隔離：`./rag_storage/company_{id}/`

### 4. 效能優化

```python
# 建立適當的索引
Index('idx_user_company_line', 'company_id', 'line_id')
Index('idx_document_company_status', 'company_id', 'status')
```

## 🔗 相關文檔

- [PostgreSQL 設置指南](./postgresql_setup.md)
- [API 架構文檔](../apps/api/ARCHITECTURE.md)
- [部署指南](../apps/api/DEPLOYMENT.md)

---

## 文檔更新

最後更新：2025年8月13日
