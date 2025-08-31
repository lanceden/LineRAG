#!/usr/bin/env python3
"""
配置詳細日誌的工具模組
"""

import logging
import sys
from datetime import datetime

def setup_detailed_logging():
    """設置詳細的日誌配置"""
    
    # 創建詳細的日誌格式
    detailed_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置根日誌器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 清除現有的處理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(console_handler)
    
    # 文件處理器
    log_filename = f"linerag_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # 配置特定模組的日誌級別
    logging.getLogger('app.services').setLevel(logging.DEBUG)
    logging.getLogger('app.routers').setLevel(logging.DEBUG)
    logging.getLogger('raganything').setLevel(logging.DEBUG)
    logging.getLogger('lightrag').setLevel(logging.DEBUG)
    
    # 減少一些噪音日誌
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    print(f"📝 詳細日誌已配置，文件: {log_filename}")
    return log_filename

def log_stage(stage_name: str, start_time: float = None):
    """記錄處理階段"""
    import time
    current_time = time.time()
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    
    if start_time:
        duration = current_time - start_time
        logging.info(f"⏱️  [{timestamp}] {stage_name} 完成 (耗時: {duration:.3f}秒)")
    else:
        logging.info(f"🚀 [{timestamp}] {stage_name} 開始")
    
    return current_time

def log_memory_usage(stage_name: str):
    """記錄記憶體使用情況"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        logging.info(f"💾 [{timestamp}] {stage_name} - 記憶體使用: {memory_mb:.1f}MB")
        
        return memory_mb
    except Exception as e:
        logging.warning(f"無法獲取記憶體信息: {e}")
        return None

if __name__ == "__main__":
    # 測試日誌配置
    setup_detailed_logging()
    
    logging.info("測試日誌配置")
    logging.debug("這是一條調試信息")
    logging.warning("這是一條警告信息")
    logging.error("這是一條錯誤信息")
    
    print("日誌配置測試完成")