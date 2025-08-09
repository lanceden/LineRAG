#!/usr/bin/env python3
"""
測試 Qdrant 本地模式是否正常工作
"""

import os
import sys
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


def test_qdrant_local():
    """測試本地 Qdrant 功能"""
    print("🧪 測試 Qdrant 本地模式...")

    try:
        # 導入必要模組
        print("✅ 成功導入 qdrant_client")

        # 測試本地客戶端
        client = QdrantClient(path="./test_qdrant")
        print("✅ 成功創建本地 Qdrant 客戶端")

        # 測試創建集合
        collection_name = "test_collection"
        try:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE),
            )
            print("✅ 成功創建測試集合")
        except Exception as e:
            if "already exists" in str(e):
                print("✅ 測試集合已存在")
            else:
                raise e

        # 測試插入向量
        import numpy as np

        test_vector = np.random.rand(128).tolist()

        client.upsert(
            collection_name=collection_name,
            points=[{"id": 1, "vector": test_vector, "payload": {"test": "data"}}],
        )
        print("✅ 成功插入測試向量")

        # 測試搜索
        search_result = client.search(
            collection_name=collection_name, query_vector=test_vector, limit=1
        )
        print(f"✅ 成功搜索，找到 {len(search_result)} 個結果")

        # 清理測試數據
        client.delete_collection(collection_name)
        print("✅ 成功清理測試數據")

        # 清理測試目錄
        import shutil

        if os.path.exists("./test_qdrant"):
            shutil.rmtree("./test_qdrant")
        print("✅ 成功清理測試目錄")

        print("\n🎉 Qdrant 本地模式測試通過！")
        print("您可以安全地使用本地模式，無需 Docker。")
        return True

    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        print("請安裝 qdrant-client: pip install qdrant-client")
        return False

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def test_embedding():
    """測試 embedding 模型"""
    print("\n🧪 測試 Embedding 模型...")

    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        embedding = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3", encode_kwargs={"normalize_embeddings": True}
        )
        print("✅ 成功載入 embedding 模型")

        # 測試編碼
        test_text = "這是一個測試文本"
        vector = embedding.embed_query(test_text)
        print(f"✅ 成功編碼文本，向量維度: {len(vector)}")

        return True

    except Exception as e:
        print(f"❌ Embedding 測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 開始測試 Qdrant 本地環境...")

    # 測試 Qdrant
    qdrant_ok = test_qdrant_local()

    # 測試 Embedding
    embedding_ok = test_embedding()

    print("\n" + "=" * 50)
    if qdrant_ok and embedding_ok:
        print("🎉 所有測試通過！您的環境已準備就緒。")
        print("\n📝 下一步:")
        print("1. 確保 ingest.py 中 USE_LOCAL_MODE = True")
        print("2. 運行 python ingest.py 開始使用")
    else:
        print("❌ 部分測試失敗，請檢查依賴安裝。")
        print("\n🔧 修復建議:")
        if not qdrant_ok:
            print("- 安裝 qdrant-client: pip install qdrant-client")
        if not embedding_ok:
            print("- 安裝相關依賴: pip install -r requirements.txt")


if __name__ == "__main__":
    main()
