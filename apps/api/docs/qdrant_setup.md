# Qdrant 設置指南

## 1. 安裝和啟動 Qdrant

### 方法 1: 使用 Docker (推薦)

```bash
# 啟動 Qdrant 服務
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

### 使用 Docker Compose

創建 `docker-compose.yml` 文件：

```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage:z
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
```

然後執行：

```bash
docker-compose up -d
```

### 方法 2: 直接安裝二進制文件

#### Windows

```bash
# 下載 Windows 版本
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-pc-windows-msvc.zip -o qdrant.zip
unzip qdrant.zip
./qdrant.exe
```

#### Linux

```bash
# 下載 Linux 版本
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz -o qdrant.tar.gz
tar -xzf qdrant.tar.gz
./qdrant
```

#### macOS

```bash
# 使用 Homebrew
brew install qdrant

# 或下載二進制文件
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-apple-darwin.tar.gz -o qdrant.tar.gz
tar -xzf qdrant.tar.gz
./qdrant
```

### 方法 3: 從源碼編譯 (需要 Rust)

```bash
# 安裝 Rust (如果還沒有)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 克隆並編譯
git clone https://github.com/qdrant/qdrant.git
cd qdrant
cargo build --release
./target/release/qdrant
```

### 方法 4: 使用 Python 內嵌模式 (僅用於開發/測試)

```python
# 修改 ingest.py 使用內嵌模式
from qdrant_client import QdrantClient

# 使用內存模式 (數據不持久化)
qdrant_client = QdrantClient(":memory:")

# 或使用本地文件存儲
qdrant_client = QdrantClient(path="./local_qdrant")
```

### 方法 5: 雲端服務

```python
# 使用 Qdrant Cloud (需要註冊帳號)
from qdrant_client import QdrantClient

qdrant_client = QdrantClient(
    url="https://your-cluster-url.qdrant.io", 
    api_key="your-api-key"
)
```

## 2. 驗證 Qdrant 運行狀態

```bash
# 檢查 Qdrant 是否正常運行
curl http://localhost:6333/health
```

應該返回：

```json
{"status":"ok"}
```

## 3. 安裝 Python 依賴

```bash
pip install qdrant-client
```

## 4. 主要變更說明

### 從 FAISS 遷移到 Qdrant 的優勢

1. **持久化存儲**：數據自動保存，無需手動 save_local()
2. **高效刪除**：支持按條件刪除，無需重建整個索引
3. **分散式支持**：可以輕鬆擴展到多節點
4. **REST API**：提供完整的 HTTP API 接口
5. **更好的過濾**：支持複雜的元數據過濾查詢

### 配置參數

- **Host**: localhost
- **Port**: 6333 (HTTP), 6334 (gRPC)
- **Collection**: documents
- **Vector Size**: 1024 (BAAI/bge-m3 模型)
- **Distance**: COSINE

## 5. 故障排除

### 如果遇到連接錯誤

1. 確認 Qdrant 服務正在運行

```bash
docker ps | grep qdrant
```

2. 檢查端口是否被占用：

```bash
netstat -an | grep 6333
  ```

3. 查看 Qdrant 日誌：
   ```bash
   docker logs <qdrant_container_id>
   ```

### 如果需要重置數據

```bash
# 停止 Qdrant
docker stop <qdrant_container_id>

# 刪除存儲數據
rm -rf qdrant_storage

# 重新啟動
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

## 6. Web UI

Qdrant 提供了 Web 管理界面：

- 訪問：[http://localhost:6333/dashboard](http://localhost:6333/dashboard)
- 可以查看集合、向量數量、執行搜索等

## 7. 性能優化建議

1. **內存設置**：為 Docker 容器分配足夠內存
2. **存儲**：使用 SSD 存儲以獲得更好性能
3. **批量操作**：大量數據時使用批量插入
4. **索引優化**：根據查詢模式調整 HNSW 參數