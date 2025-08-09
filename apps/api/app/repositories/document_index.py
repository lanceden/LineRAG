from __future__ import annotations
import json
import os
import time
from typing import List, Dict, Any

# 定義索引目錄和索引檔案的路徑
INDEX_DIR = "./qdrant_data"
INDEX_FILE = os.path.join(INDEX_DIR, "doc_index.json")


def load_document_index() -> List[Dict[str, Any]]:
    """
    從 JSON 檔案載入文件索引。
    如果索引檔案存在，則讀取並返回其內容；否則返回空列表。
    """
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_document_index(doc_index: List[Dict[str, Any]]):
    """
    將文件索引儲存到 JSON 檔案。
    如果索引目錄不存在，則創建它。
    """
    os.makedirs(INDEX_DIR, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(doc_index, f, ensure_ascii=False, indent=2)
