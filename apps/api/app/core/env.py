"""
環境變數載入器 - 匯入一次以載入 .env
"""

from dotenv import load_dotenv

# 當此模組被匯入時，載入 .env 檔案一次
load_dotenv()
