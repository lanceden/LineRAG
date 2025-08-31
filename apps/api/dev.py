#!/usr/bin/env python
"""
FastAPI 開發調試腳本
用於在 monorepo 環境下方便地啟動和調試 FastAPI
"""
import uvicorn
import os
import sys

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    print("🚀 啟動 FastAPI 開發服務器...")
    try:
        print("📂 工作目錄:", os.getcwd())
    except Exception as e:
        print("📂 無法獲取工作目錄:", e)
    print("🔗 API 文檔: http://localhost:8000/docs")
    print("❤️  健康檢查: http://localhost:8000/health")
    print("---")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
    )
