# FastAPI Debug 指南 (Monorepo)

## 方法一：VS Code Debug 配置

### 1. 創建 VS Code 設定

在專案根目錄創建 `.vscode/launch.json`：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug FastAPI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/apps/api/main.py",
            "args": [],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}/apps/api",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/apps/api"
            },
            "python": "${workspaceFolder}/apps/api/.venv/bin/python"
        },
        {
            "name": "Debug FastAPI with Uvicorn",
            "type": "python", 
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000"
            ],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}/apps/api",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/apps/api"
            }
        }
    ]
}
```

### 2. 使用步驟

1. 在 VS Code 中打開專案根目錄
2. 在 FastAPI 代碼中設置斷點
3. 按 `F5` 或選擇 "Run and Debug"
4. 選擇 "Debug FastAPI with Uvicorn"
5. 訪問 `http://localhost:8000` 觸發斷點

## 方法二：直接運行 Debug

### 在 `apps/api/main.py` 中添加

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
```

然後直接運行：

```bash
cd apps/api
python main.py
```

## 方法三：使用 debugpy

### 1. 安裝 debugpy

```bash
cd apps/api
pip install debugpy
```

### 2. 在代碼中添加調試器

```python
# 在 main.py 開頭添加
import debugpy

# 等待調試器連接
debugpy.listen(("0.0.0.0", 5678))
print("Waiting for debugger attach...")
debugpy.wait_for_client()
print("Debugger attached!")
```

### 3. VS Code 連接配置

```json
{
    "name": "Python: Remote Attach",
    "type": "python",
    "request": "attach",
    "connect": {
        "host": "localhost",
        "port": 5678
    },
    "pathMappings": [
        {
            "localRoot": "${workspaceFolder}/apps/api",
            "remoteRoot": "."
        }
    ]
}
```

## 方法四：使用 pdb

### 在代碼中直接添加斷點

```python
import pdb; pdb.set_trace()
```

然後用命令行運行：

```bash
cd apps/api
uvicorn main:app --reload
```

## 開發腳本

### 創建 `apps/api/dev.py`

```python
#!/usr/bin/env python
"""
FastAPI 開發調試腳本
"""
import uvicorn
import os
import sys

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
        access_log=True
    )
```

使用：

```bash
cd apps/api
python dev.py
```

## PyCharm Debug 配置

### Run Configuration 設定

1. **Script path**: `apps/api/main.py`
2. **Working directory**: `apps/api`
3. **Environment variables**:
   - `PYTHONPATH=apps/api`
4. **Python interpreter**: 使用虛擬環境

或使用 Uvicorn 配置：

1. **Module name**: `uvicorn`
2. **Parameters**: `main:app --reload --host 0.0.0.0 --port 8000`
3. **Working directory**: `apps/api`

## Docker Debug

### 創建 `apps/api/Dockerfile.debug`

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install debugpy

COPY . .

EXPOSE 8000 5678

CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### docker-compose.debug.yml

```yaml
version: '3.8'
services:
  api-debug:
    build:
      context: ./apps/api
      dockerfile: Dockerfile.debug
    ports:
      - "8000:8000"
      - "5678:5678"  # debugpy port
    volumes:
      - ./apps/api:/app
    environment:
      - LOG_LEVEL=DEBUG
```

## 日誌 Debug

### 增強日誌設定

```python
import logging
import sys

# 設定詳細日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log')
    ]
)

logger = logging.getLogger(__name__)
```

### 使用 rich 美化日誌

```bash
pip install rich
```

```python
from rich.logging import RichHandler
import logging

logging.basicConfig(
    level="DEBUG",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
```

## 監控工具

### 1. FastAPI 內建工具

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### 2. 添加 Debug 中間件

```python
import time
from fastapi import Request

@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"{request.method} {request.url} - {response.status_code} - {process_time:.4f}s")
    return response
```

## 常用 Debug 命令

```bash
# 檢查依賴
cd apps/api && pip list

# 驗證環境變數
cd apps/api && python -c "import os; print(os.getenv('EMBEDDING_MODEL_NAME'))"

# 測試 API 端點
curl -X GET http://localhost:8000/health

# 檢查日誌
tail -f apps/api/debug.log

# 測試特定路由
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "parts": [{"type": "text", "text": "Hello"}]}]}'
```

## 推薦的 Debug 工作流

1. **開發階段**: 使用 VS Code Debug 配置
2. **API 測試**: 使用 Swagger UI (`/docs`)
3. **問題排查**: 添加詳細日誌
4. **性能分析**: 使用 Debug 中間件
5. **生產 Debug**: 使用 Docker debug 配置

---
