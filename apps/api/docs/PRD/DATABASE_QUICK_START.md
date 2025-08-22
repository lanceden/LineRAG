# Python 資料庫管理快速入門

## 🚀 快速使用

### 第一次部署（推薦）

```bash
# 進入 API 目錄
cd apps/api

# 一鍵初始化（自動建立資料庫+資料表+範例資料）
python init_db.py
```

### 開發中修改模型後

```bash
# 1. 創建遷移
alembic revision --autogenerate -m "描述變更"

# 2. 執行遷移
alembic upgrade head
```

### 使用輔助腳本（高級用途）

```bash
# 進入專案目錄
cd c:\Users\lance\Downloads\repo\LineRAG

# 執行資料庫管理腳本
python db_manager.py
```

## 📋 常用操作清單

### 每次修改 Model 後

1. 創建遷移

   ```bash
   alembic revision --autogenerate -m "添加新欄位"
   ```

2. 執行遷移

   ```bash
   alembic upgrade head
   ```

### 專案首次部署

1. **確保PostgreSQL服務運行**

2. **配置環境變數**

   ```bash
   # 確保 .env 檔案包含
   DATABASE_URL=postgresql://postgres:password@localhost:5432/linerag
   ```

3. **一鍵初始化**

   ```bash
   cd apps/api
   python init_db.py  # 自動建立資料庫+資料表+範例資料
   ```

4. **啟動服務**

   ```bash
   docker-compose up -d
   ```

### 故障排除

1. 遷移衝突

   ```bash
   alembic stamp head  # 強制標記為最新
   ```

2. 重置遷移

   ```bash
   alembic downgrade base  # 回到初始狀態
   alembic upgrade head    # 重新執行所有遷移
   ```

## 🔄 與其他工具比較

| 操作     | Prisma                  | Entity Framework               | Alembic + SQLAlchemy                        |
| -------- | ----------------------- | ------------------------------ | ------------------------------------------- |
| 初始化   | `prisma init`           | `Add-Migration Initial`        | `alembic init alembic`                      |
| 創建遷移 | `prisma migrate dev`    | `Add-Migration Name`           | `alembic revision --autogenerate -m "Name"` |
| 執行遷移 | 自動執行                | `Update-Database`              | `alembic upgrade head`                      |
| 查看狀態 | `prisma migrate status` | `Get-Migrations`               | `alembic current`                           |
| 重置     | `prisma migrate reset`  | `Update-Database -Migration 0` | `alembic downgrade base`                    |

## 📁 檔案結構

```text
LineRAG/
├── db_manager.py          # 資料庫管理輔助腳本
├── docs/
│   └── database_management.md  # 完整文檔
└── apps/api/
    ├── alembic/           # Alembic 配置和遷移檔案
    │   ├── versions/      # 遷移版本檔案
    │   ├── env.py        # Alembic 環境配置
    │   └── script.py.mako # 遷移模板
    ├── alembic.ini       # Alembic 主配置
    ├── init_db.py        # 資料庫初始化腳本
    └── app/models/       # SQLAlchemy 模型
        ├── company.py
        ├── user.py
        └── document.py
```

## 🎯 最佳實踐

1. **第一次部署直接用 `python init_db.py`** - 自動化程度最高
2. **每次修改 Model 都要創建遷移**
3. **遷移描述要清楚明確**
4. **測試環境先驗證遷移**
5. **備份生產資料庫再執行遷移**
6. **使用版本控制管理遷移檔案**

## ✨ 自動化功能

- **自動建立資料庫**: 第一次匯入模型時自動建立 `linerag` 資料庫
- **自動建立資料表**: `init_db.py` 會呼叫 `create_tables()`
- **自動建立範例資料**: 示範公司和管理員帳戶
- **環境變數自動載入**: 支援 `.env` 檔案配置

---

詳細文檔請參考：[database_management.md](./docs/database_management.md)
