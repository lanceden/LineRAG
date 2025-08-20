#!/usr/bin/env python3
"""
快速清空 Qdrant 和 Neo4j 數據庫 (無需確認)
使用方法：python quick_clear.py
"""

import os
import sys
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def check_environment():
    """檢查運行環境"""
    print(f"🔍 Python 路徑: {sys.executable}")
    print(f"🔍 工作目錄: {os.getcwd()}")
    
    # 檢查套件
    try:
        import qdrant_client
        print(f"✅ qdrant_client 可用")
    except ImportError:
        print(f"❌ qdrant_client 不可用")
    
    try:
        import neo4j
        print(f"✅ neo4j 可用")
    except ImportError:
        print(f"❌ neo4j 不可用")
        print(f"💡 請確保使用正確的conda環境：conda activate line-rag-api")

def quick_clear():
    """快速清空所有數據"""
    print("快速清空數據庫...")
    
    qdrant_success = False
    neo4j_success = False
    
    # 清空 Qdrant (包含LightRAG默認集合)
    try:
        from qdrant_client import QdrantClient
        
        qdrant_client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
        )
        
        collections = qdrant_client.get_collections()
        deleted = 0
        total_points = 0
        
        print(f"找到 {len(collections.collections)} 個集合:")
        for collection in collections.collections:
            try:
                info = qdrant_client.get_collection(collection.name)
                points_count = info.points_count
                total_points += points_count
                print(f"  - 刪除: {collection.name} ({points_count} 個向量點)")
                qdrant_client.delete_collection(collection.name)
                deleted += 1
            except Exception as e:
                print(f"  - 刪除失敗: {collection.name} ({e})")
        
        print(f"Qdrant: 清空 {deleted} 個集合, {total_points} 個向量點")
        qdrant_success = True
        
    except Exception as e:
        print(f"Qdrant 清空失敗: {e}")
    
    # 清空 Neo4j
    try:
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USERNAME", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "linerag123"),
            ),
        )
        
        with driver.session() as session:
            result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted")
            deleted_count = result.single()["deleted"]
            print(f"✅ Neo4j: 刪除 {deleted_count} 個節點")
        
        driver.close()
        neo4j_success = True
        
    except Exception as e:
        print(f"❌ Neo4j 清空失敗: {e}")
    
    # 結果
    if qdrant_success and neo4j_success:
        print("🎉 數據庫清空完成！")
    else:
        print("⚠️  部分清空失敗")

if __name__ == "__main__":
    print("🔧 環境檢查...")
    check_environment()
    print()
    quick_clear()