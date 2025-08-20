import logging
import os
from dotenv import load_dotenv

load_dotenv()


def setup_logging() -> logging.Logger:
    """
    設定日誌記錄器。
    根據環境變數 LOG_LEVEL 設定日誌級別，預設為 INFO。
    格式為：時間 級別 [日誌名稱] 訊息
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    
    # 抑制第三方庫的DEBUG日誌
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger = logging.getLogger("linerag")
    return logger
