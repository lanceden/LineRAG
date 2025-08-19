# LineRAG 備份策略指南

## 📋 概述

LineRAG 智能客服系統的備份策略包含多個層面的數據保護，確保系統在各種故障情況下都能快速恢復服務。

## 🎯 備份目標

- **Recovery Time Objective (RTO)**: < 30 分鐘
- **Recovery Point Objective (RPO)**: < 24 小時
- **備份保留期**: 30 天（本地）+ 90 天（雲端）
- **備份驗證**: 每周執行恢復測試

---

## 🗂️ 備份範圍

### 1. **Neo4j 知識圖譜數據庫**

- 圖數據庫文件
- 配置文件
- 用戶定義程序和插件

### 2. **PostgreSQL 關聯數據庫**

- 用戶資料、公司資料
- 系統配置、權限設定
- 審計日誌、使用統計

### 3. **文件系統數據**

- RAG 處理文件 (`./rag_storage/`)
- 用戶上傳文檔 (`./uploads/`)
- 系統配置文件

### 4. **容器配置**

- Docker Compose 配置
- 環境變數配置
- Nginx 配置

---

## 🔧 備份配置

### Docker Compose 配置調整

確保 `docker-compose.yml` 包含備份卷映射：

```yaml
neo4j:
  volumes:
    - ./neo4j_data:/data
    - ./neo4j_logs:/logs
    - ./backups/neo4j:/backups  # 備份目錄

volumes:
  backups:
    driver: local
```

### 創建備份目錄結構

```bash
# 創建備份目錄
mkdir -p backups/{neo4j,postgres,files,configs}
mkdir -p backups/archive/{daily,weekly,monthly}
```

---

## 📜 備份腳本

### 1. Neo4j 數據庫備份

創建 `scripts/backup-neo4j.sh`：

```bash
#!/bin/bash
# Neo4j 數據庫備份腳本

set -e

# 配置
DATE=$(date +"%Y%m%d_%H%M%S")
CONTAINER_NAME="linerag-neo4j"
BACKUP_DIR="./backups/neo4j"
LOG_FILE="./backups/backup-neo4j.log"

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "開始 Neo4j 備份..."

# 檢查容器運行狀態
if ! docker ps | grep -q $CONTAINER_NAME; then
    log "錯誤: Neo4j 容器未運行"
    exit 1
fi

# 執行數據庫備份
log "執行數據庫 dump..."
docker exec $CONTAINER_NAME neo4j-admin database dump neo4j \
  --to-path=/backups \
  --compress=true

# 重命名備份文件
if [ $? -eq 0 ]; then
    docker exec $CONTAINER_NAME mv /backups/neo4j.dump /backups/neo4j_$DATE.dump
    log "Neo4j 備份完成: neo4j_$DATE.dump"
else
    log "錯誤: Neo4j 備份失敗"
    exit 1
fi

# 清理舊備份（保留 7 天）
log "清理舊備份文件..."
find $BACKUP_DIR -name "neo4j_*.dump" -mtime +7 -delete

log "Neo4j 備份流程完成"
```

### 2. PostgreSQL 數據庫備份

創建 `scripts/backup-postgres.sh`：

```bash
#!/bin/bash
# PostgreSQL 數據庫備份腳本

set -e

# 配置
DATE=$(date +"%Y%m%d_%H%M%S")
DB_HOST="localhost"
DB_NAME="linerag"
DB_USER="postgres"
BACKUP_DIR="./backups/postgres"
LOG_FILE="./backups/backup-postgres.log"

# 確保備份目錄存在
mkdir -p $BACKUP_DIR

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "開始 PostgreSQL 備份..."

# 執行數據庫備份
BACKUP_FILE="$BACKUP_DIR/linerag_$DATE.sql"

if pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -f $BACKUP_FILE; then
    # 壓縮備份文件
    gzip $BACKUP_FILE
    log "PostgreSQL 備份完成: linerag_$DATE.sql.gz"
    
    # 清理舊備份（保留 30 天）
    find $BACKUP_DIR -name "linerag_*.sql.gz" -mtime +30 -delete
    log "清理舊備份完成"
else
    log "錯誤: PostgreSQL 備份失敗"
    exit 1
fi

log "PostgreSQL 備份流程完成"
```

### 3. 文件系統備份

創建 `scripts/backup-files.sh`：

```bash
#!/bin/bash
# 文件系統備份腳本

set -e

# 配置
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="./backups/files"
LOG_FILE="./backups/backup-files.log"

# 確保備份目錄存在
mkdir -p $BACKUP_DIR

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "開始文件系統備份..."

# 備份 RAG 存儲目錄
if [ -d "./rag_storage" ]; then
    log "備份 RAG 存儲..."
    tar -czf $BACKUP_DIR/rag_storage_$DATE.tar.gz ./rag_storage/
fi

# 備份用戶上傳文件
if [ -d "./uploads" ]; then
    log "備份用戶上傳文件..."
    tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz ./uploads/
fi

# 備份配置文件
log "備份配置文件..."
tar -czf $BACKUP_DIR/configs_$DATE.tar.gz \
  ./docker-compose.yml \
  ./.env* \
  ./nginx.conf* \
  2>/dev/null || true

# 清理舊備份（保留 14 天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +14 -delete

log "文件系統備份完成"
```

### 4. 完整系統備份

創建 `scripts/backup-full.sh`：

```bash
#!/bin/bash
# 完整系統備份腳本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="./backups/backup-full.log"

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "========== 開始完整系統備份 =========="

# 執行各項備份
log "1. 執行 Neo4j 備份..."
bash $SCRIPT_DIR/backup-neo4j.sh

log "2. 執行 PostgreSQL 備份..."
bash $SCRIPT_DIR/backup-postgres.sh

log "3. 執行文件系統備份..."
bash $SCRIPT_DIR/backup-files.sh

# 創建備份清單
log "4. 創建備份清單..."
DATE=$(date +"%Y%m%d_%H%M%S")
MANIFEST="./backups/backup_manifest_$DATE.txt"

echo "LineRAG 系統備份清單" > $MANIFEST
echo "備份時間: $(date)" >> $MANIFEST
echo "===========================================" >> $MANIFEST
echo "" >> $MANIFEST

echo "Neo4j 備份:" >> $MANIFEST
ls -la ./backups/neo4j/ | tail -5 >> $MANIFEST
echo "" >> $MANIFEST

echo "PostgreSQL 備份:" >> $MANIFEST  
ls -la ./backups/postgres/ | tail -5 >> $MANIFEST
echo "" >> $MANIFEST

echo "文件備份:" >> $MANIFEST
ls -la ./backups/files/ | tail -5 >> $MANIFEST

log "備份清單已創建: $MANIFEST"

log "========== 完整系統備份完成 =========="
```

---

## ⏰ 定時備份配置

### Crontab 設定

```bash
# 編輯 crontab
crontab -e

# 每日凌晨 2:00 執行完整備份
0 2 * * * /path/to/LineRAG/scripts/backup-full.sh

# 每 6 小時備份 Neo4j（高頻）
0 */6 * * * /path/to/LineRAG/scripts/backup-neo4j.sh

# 每周日凌晨 1:00 執行系統維護
0 1 * * 0 /path/to/LineRAG/scripts/maintenance.sh
```

### Windows 任務排程器

```powershell
# 創建每日備份任務
schtasks /create /tn "LineRAG-Daily-Backup" /tr "C:\path\to\backup-full.sh" /sc daily /st 02:00
```

---

## ☁️ 雲端備份

### AWS S3 同步

創建 `scripts/sync-to-s3.sh`：

```bash
#!/bin/bash
# S3 雲端同步腳本

# 配置
S3_BUCKET="your-bucket-name"
AWS_PROFILE="default"
LOCAL_BACKUP_DIR="./backups"
LOG_FILE="./backups/s3-sync.log"

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "開始同步到 AWS S3..."

# 同步到 S3
aws s3 sync $LOCAL_BACKUP_DIR s3://$S3_BUCKET/linerag-backups/ \
  --profile $AWS_PROFILE \
  --storage-class STANDARD_IA \
  --delete

if [ $? -eq 0 ]; then
    log "S3 同步完成"
else
    log "錯誤: S3 同步失敗"
    exit 1
fi
```

---

## 🔄 災難恢復程序

### 1. Neo4j 恢復

```bash
#!/bin/bash
# Neo4j 災難恢復腳本

BACKUP_FILE="$1"
CONTAINER_NAME="linerag-neo4j"

if [ -z "$BACKUP_FILE" ]; then
    echo "使用方法: $0 <備份檔案>"
    exit 1
fi

echo "開始 Neo4j 恢復..."

# 停止 Neo4j 服務
docker-compose stop neo4j

# 清空現有數據
sudo rm -rf ./neo4j_data/*

# 恢復數據庫
docker run --rm \
  -v $(pwd)/neo4j_data:/data \
  -v $(pwd)/backups/neo4j:/backups \
  neo4j:5.20 \
  neo4j-admin database load neo4j --from-path=/backups/$BACKUP_FILE

# 重啟服務
docker-compose start neo4j

echo "Neo4j 恢復完成"
```

### 2. PostgreSQL 恢復

```bash
#!/bin/bash
# PostgreSQL 災難恢復腳本

BACKUP_FILE="$1"
DB_NAME="linerag"

if [ -z "$BACKUP_FILE" ]; then
    echo "使用方法: $0 <備份檔案>"
    exit 1
fi

echo "開始 PostgreSQL 恢復..."

# 解壓備份文件（如果是 .gz）
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | psql -U postgres -d $DB_NAME
else
    psql -U postgres -d $DB_NAME < $BACKUP_FILE
fi

echo "PostgreSQL 恢復完成"
```

### 3. Docker Image 還原

當 Docker Image 損壞或丟失時的完整還原程序：

#### 方案 A：從 Docker Hub 重新拉取

```bash
#!/bin/bash
# Docker Image 還原腳本 (方案A)

echo "開始 Docker Image 還原..."

# 停止所有服務
docker-compose down

# 清除損壞的 Image
docker rmi neo4j:5.20 qdrant/qdrant:v1.7.4 || true

# 重新拉取 Image
docker pull neo4j:5.20
docker pull qdrant/qdrant:v1.7.4

# 重建自定義 Image
docker-compose build --no-cache api web

# 重啟服務
docker-compose up -d

echo "Docker Image 還原完成"
```

#### 方案 B：從備份的 Image 還原

```bash
#!/bin/bash
# Docker Image 備份腳本

DATE=$(date +"%Y%m%d")
BACKUP_DIR="./backups/images"

mkdir -p $BACKUP_DIR

echo "備份 Docker Images..."

# 備份關鍵 Images
docker save neo4j:5.20 | gzip > $BACKUP_DIR/neo4j_5.20_$DATE.tar.gz
docker save qdrant/qdrant:v1.7.4 | gzip > $BACKUP_DIR/qdrant_v1.7.4_$DATE.tar.gz

# 備份自建 Images
docker save linerag-api:latest | gzip > $BACKUP_DIR/linerag-api_$DATE.tar.gz || true
docker save linerag-web:latest | gzip > $BACKUP_DIR/linerag-web_$DATE.tar.gz || true

echo "Docker Image 備份完成"
```

```bash
#!/bin/bash
# Docker Image 還原腳本 (方案B)

BACKUP_DIR="./backups/images"
IMAGE_FILE="$1"

if [ -z "$IMAGE_FILE" ]; then
    echo "使用方法: $0 <image_backup_file.tar.gz>"
    echo "可用備份檔案:"
    ls -la $BACKUP_DIR/*.tar.gz
    exit 1
fi

echo "從備份還原 Docker Image: $IMAGE_FILE"

# 停止相關服務
docker-compose down

# 載入 Image
gunzip -c $BACKUP_DIR/$IMAGE_FILE | docker load

# 重啟服務
docker-compose up -d

echo "Docker Image 還原完成"
```

### 4. 完整災難恢復程序

創建 `scripts/disaster-recovery.sh`：

```bash
#!/bin/bash
# 完整災難恢復腳本

set -e

BACKUP_DATE="$1"
LOG_FILE="./backups/disaster-recovery.log"

if [ -z "$BACKUP_DATE" ]; then
    echo "使用方法: $0 <備份日期 YYYYMMDD>"
    echo "例如: $0 20250118"
    exit 1
fi

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "========== 開始災難恢復程序 =========="
log "恢復日期: $BACKUP_DATE"

# 步驟 1: 停止所有服務
log "1. 停止所有服務..."
docker-compose down

# 步驟 2: 清理現有數據
log "2. 清理現有數據..."
read -p "警告: 這將刪除所有現有數據，確定繼續嗎? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log "災難恢復已取消"
    exit 1
fi

sudo rm -rf ./neo4j_data/* ./rag_storage/* ./uploads/*

# 步驟 3: 還原 Docker Images
log "3. 還原 Docker Images..."
if [ -f "./backups/images/neo4j_5.20_$BACKUP_DATE.tar.gz" ]; then
    gunzip -c "./backups/images/neo4j_5.20_$BACKUP_DATE.tar.gz" | docker load
fi

# 步驟 4: 還原 Neo4j 數據
log "4. 還原 Neo4j 數據..."
NEO4J_BACKUP=$(find ./backups/neo4j -name "neo4j_${BACKUP_DATE}_*.dump" | head -1)
if [ -f "$NEO4J_BACKUP" ]; then
    docker run --rm \
      -v $(pwd)/neo4j_data:/data \
      -v $(pwd)/backups/neo4j:/backups \
      neo4j:5.20 \
      neo4j-admin database load neo4j --from-path=/backups/$(basename $NEO4J_BACKUP)
    log "Neo4j 數據還原完成"
else
    log "警告: 找不到 Neo4j 備份文件"
fi

# 步驟 5: 還原 PostgreSQL 數據
log "5. 還原 PostgreSQL 數據..."
PG_BACKUP=$(find ./backups/postgres -name "linerag_${BACKUP_DATE}_*.sql.gz" | head -1)
if [ -f "$PG_BACKUP" ]; then
    # 需要 PostgreSQL 服務先運行
    docker-compose up -d postgres
    sleep 30
    gunzip -c "$PG_BACKUP" | docker exec -i linerag-postgres psql -U postgres -d linerag
    log "PostgreSQL 數據還原完成"
else
    log "警告: 找不到 PostgreSQL 備份文件"
fi

# 步驟 6: 還原文件系統
log "6. 還原文件系統..."
if [ -f "./backups/files/rag_storage_${BACKUP_DATE}.tar.gz" ]; then
    tar -xzf "./backups/files/rag_storage_${BACKUP_DATE}.tar.gz"
fi
if [ -f "./backups/files/uploads_${BACKUP_DATE}.tar.gz" ]; then
    tar -xzf "./backups/files/uploads_${BACKUP_DATE}.tar.gz"
fi

# 步驟 7: 還原配置文件
log "7. 還原配置文件..."
if [ -f "./backups/files/configs_${BACKUP_DATE}.tar.gz" ]; then
    tar -xzf "./backups/files/configs_${BACKUP_DATE}.tar.gz"
fi

# 步驟 8: 重啟所有服務
log "8. 重啟所有服務..."
docker-compose up -d

# 步驟 9: 驗證恢復
log "9. 驗證系統恢復..."
sleep 60

# 檢查服務狀態
if docker-compose ps | grep -q "Up"; then
    log "✅ 服務恢復成功"
else
    log "❌ 服務恢復失敗，請檢查日誌"
fi

# 檢查數據庫連接
if docker exec linerag-neo4j cypher-shell -u neo4j -p linerag123 "RETURN 1" >/dev/null 2>&1; then
    log "✅ Neo4j 連接正常"
else
    log "❌ Neo4j 連接失敗"
fi

log "========== 災難恢復程序完成 =========="
log "請檢查系統功能並進行完整測試"
```

---

## 📊 監控和告警

### 備份監控腳本

創建 `scripts/backup-monitor.sh`：

```bash
#!/bin/bash
# 備份監控腳本

BACKUP_DIR="./backups"
ALERT_EMAIL="admin@yourcompany.com"
LOG_FILE="./backups/monitor.log"

# 檢查函數
check_backup() {
    local backup_type=$1
    local max_age=$2
    local backup_path="$BACKUP_DIR/$backup_type"
    
    if [ ! -d "$backup_path" ]; then
        echo "警告: 備份目錄不存在 - $backup_path"
        return 1
    fi
    
    latest_backup=$(find $backup_path -type f -mtime -$max_age | wc -l)
    
    if [ $latest_backup -eq 0 ]; then
        echo "警告: $max_age 天內沒有 $backup_type 備份"
        return 1
    fi
    
    echo "正常: $backup_type 備份狀態良好"
    return 0
}

# 執行檢查
echo "開始備份監控檢查..." | tee -a $LOG_FILE

# 檢查 Neo4j 備份（24小時內）
check_backup "neo4j" 1

# 檢查 PostgreSQL 備份（24小時內）  
check_backup "postgres" 1

# 檢查文件備份（48小時內）
check_backup "files" 2

echo "備份監控檢查完成" | tee -a $LOG_FILE
```

---

## 📝 維護計劃

### 每日維護
- ✅ 自動備份執行
- ✅ 備份文件完整性檢查
- ✅ 舊備份文件清理

### 每周維護  
- ✅ 備份恢復測試
- ✅ 存儲空間檢查
- ✅ 雲端同步驗證

### 每月維護
- ✅ 災難恢復演練
- ✅ 備份策略評估
- ✅ 存儲成本優化

---

## 🛠️ 使用指南

### 執行備份

```bash
# 執行完整備份
./scripts/backup-full.sh

# 只備份 Neo4j
./scripts/backup-neo4j.sh

# 備份 Docker Images
./scripts/backup-images.sh

# 同步到雲端
./scripts/sync-to-s3.sh
```

### 災難恢復

#### 一般數據恢復

```bash
# 恢復 Neo4j
./scripts/restore-neo4j.sh neo4j_20250118_020000.dump

# 恢復 PostgreSQL
./scripts/restore-postgres.sh linerag_20250118_020000.sql.gz
```

#### Docker Image 恢復

```bash
# 方案 A: 從 Docker Hub 重新下載
./scripts/restore-images-online.sh

# 方案 B: 從備份恢復
./scripts/restore-images-backup.sh neo4j_5.20_20250118.tar.gz

# 檢查 Images 狀態
docker images | grep -E "(neo4j|qdrant|linerag)"
```

#### 完整災難恢復

```bash
# 一鍵完整恢復（謹慎使用）
./scripts/disaster-recovery.sh 20250118

# 分步驟恢復
# 1. 先恢復 Images
./scripts/restore-images-online.sh
# 2. 再恢復數據
./scripts/restore-neo4j.sh neo4j_20250118_020000.dump
# 3. 最後恢復文件
tar -xzf ./backups/files/rag_storage_20250118.tar.gz
```

### 監控檢查

```bash
# 檢查備份狀態
./scripts/backup-monitor.sh

# 查看備份日誌
tail -f ./backups/backup-full.log
```

---

## 🚨 緊急故障處理

### 常見 Docker Image 故障情況

#### 1. **Image 損壞無法啟動**

```bash
# 症狀：容器啟動失敗，錯誤提示 "image not found" 或 "corrupted"

# 快速修復
docker-compose down
docker system prune -f
docker pull neo4j:5.20
docker pull qdrant/qdrant:v1.7.4
docker-compose up -d
```

#### 2. **磁碟空間不足導致 Image 損壞**

```bash
# 症狀：docker pull 失敗，或容器異常退出

# 清理空間
docker system df  # 檢查空間使用
docker system prune -af  # 清理未使用資源
docker volume prune  # 清理未使用的 volumes

# 重新拉取
docker-compose pull
docker-compose up -d
```

#### 3. **Registry 連接失敗**

```bash
# 症狀：無法從 Docker Hub 拉取 Image

# 使用本地備份
cd backups/images
ls *.tar.gz  # 查看可用備份

# 載入最新備份
gunzip -c neo4j_5.20_latest.tar.gz | docker load
gunzip -c qdrant_v1.7.4_latest.tar.gz | docker load

# 重啟服務
docker-compose up -d
```

#### 4. **完全系統故障**

```bash
# 症狀：所有容器都無法啟動，數據可能損壞

# 使用災難恢復
./scripts/disaster-recovery.sh $(date -d '1 day ago' +%Y%m%d)

# 或手動恢復
# 1. 重裝 Docker 
# 2. 恢復 Images
# 3. 恢復數據
# 4. 恢復配置
```

### 恢復時間估算

| 故障類型         | 恢復時間   | 數據損失 |
| ---------------- | ---------- | -------- |
| Image 重新下載   | 5-10 分鐘  | 無       |
| 從備份恢復 Image | 2-5 分鐘   | 無       |
| Neo4j 數據恢復   | 10-30 分鐘 | < 24小時 |
| 完整系統恢復     | 30-60 分鐘 | < 24小時 |

---

## 📞 緊急聯絡

- **系統管理員**: [lance.den@outlook.com](mailto:lance.den@outlook.com)

---
