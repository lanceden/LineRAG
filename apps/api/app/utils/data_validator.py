"""
數據驗證工具
"""

import os
from typing import Dict, Any, Optional
from .namespace import get_company_workspace


async def verify_document_processing(company_id: int, document_name: str) -> bool:
    """驗證文檔是否正確處理"""
    workspace = get_company_workspace(company_id)
    print(f"🔍 驗證文檔處理狀態 - 公司: {company_id}, 文檔: {document_name}")
    print(f"   命名空間: {workspace}")

    # 檢查 Qdrant
    qdrant_valid = await check_qdrant_data(workspace)
    print(f"   📊 Qdrant 數據有效: {qdrant_valid}")

    # 檢查 Neo4j
    neo4j_valid = await check_neo4j_data(workspace)
    print(f"   🔗 Neo4j 數據有效: {neo4j_valid}")

    result = qdrant_valid and neo4j_valid
    print(f"   ✅ 整體驗證結果: {result}")

    return result


async def verify_query_data_exists(company_id: int) -> bool:
    """驗證查詢數據是否存在"""
    workspace = get_company_workspace(company_id)
    print(f"🔍 驗證查詢數據存在性 - 公司: {company_id}")
    print(f"   命名空間: {workspace}")

    # 檢查 Qdrant 數據 - 這是 RAG 查詢的必要條件
    has_vector_data = await has_qdrant_data(workspace)
    if not has_vector_data:
        print(f"   ⚠️  警告: 命名空間 {workspace} 中沒有向量數據")
        return False

    # 檢查 Neo4j 數據 - 這是可選的，沒有圖數據也可以進行 RAG 查詢
    has_graph_data = await has_neo4j_data(workspace)
    if not has_graph_data:
        print(f"   ⚠️  警告: 命名空間 {workspace} 中沒有圖數據，但仍可進行向量查詢")
    else:
        print(f"   ✅ 發現圖數據，可進行增強查詢")

    print(f"   ✅ 查詢數據驗證通過 (基於向量數據)")
    return True


async def check_qdrant_data(workspace: str) -> bool:
    """檢查 Qdrant 中是否有有效數據"""
    try:
        from qdrant_client import QdrantClient

        qdrant_client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
        )

        collections = qdrant_client.get_collections()
        workspace_collections = [
            c for c in collections.collections if workspace in c.name
        ]

        if not workspace_collections:
            print(f"      ❌ 沒有找到命名空間 {workspace} 的集合")
            return False

        total_points = 0
        for collection in workspace_collections:
            try:
                info = qdrant_client.get_collection(collection.name)
                points_count = info.points_count
                total_points += points_count
                print(f"      📦 {collection.name}: {points_count} 個向量點")
            except Exception as e:
                print(f"      ❌ 集合 {collection.name} 檢查失敗: {e}")
                return False

        if total_points == 0:
            print(f"      ⚠️  警告: 命名空間中沒有向量點")
            return False

        print(f"      ✅ Qdrant 總向量點數: {total_points}")
        return True

    except Exception as e:
        print(f"      ❌ Qdrant 連接失敗: {e}")
        return False


async def check_neo4j_data(workspace: str) -> bool:
    """檢查 Neo4j 中是否有有效數據"""
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
            # 先嘗試查詢有workspace屬性的節點
            result = session.run(
                "MATCH (n) WHERE n.workspace = $workspace RETURN count(n) as node_count",
                workspace=workspace,
            )
            node_count = result.single()["node_count"]
            print(f"      🔗 Neo4j 節點數 (帶workspace): {node_count}")

            # 如果沒有找到帶workspace的節點，檢查是否有任何節點（向後兼容）
            if node_count == 0:
                result = session.run("MATCH (n) RETURN count(n) as total_count")
                total_count = result.single()["total_count"]
                print(f"      🔗 Neo4j 總節點數: {total_count}")
                
                if total_count > 0:
                    print(f"      ⚠️  發現節點但缺少workspace屬性，可能是舊數據")
                    # 對於向後兼容，我們認為有節點就是有效的
                    return True
                else:
                    print(f"      ⚠️  警告: 命名空間中沒有圖節點")
                    return False

        driver.close()
        return True

    except Exception as e:
        print(f"      ❌ Neo4j 連接失敗: {e}")
        return False


async def has_qdrant_data(workspace: str) -> bool:
    """檢查 Qdrant 中是否有數據"""
    try:
        from qdrant_client import QdrantClient

        qdrant_client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
        )

        collections = qdrant_client.get_collections()
        workspace_collections = [
            c for c in collections.collections if workspace in c.name
        ]

        for collection in workspace_collections:
            try:
                info = qdrant_client.get_collection(collection.name)
                if info.points_count > 0:
                    return True
            except:
                continue

        return False

    except Exception:
        return False


async def has_neo4j_data(workspace: str) -> bool:
    """檢查 Neo4j 中是否有數據"""
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
            # 先嘗試查詢有workspace屬性的節點
            result = session.run(
                "MATCH (n) WHERE n.workspace = $workspace RETURN count(n) as node_count",
                workspace=workspace,
            )
            node_count = result.single()["node_count"]
            
            # 如果沒有找到帶workspace的節點，檢查是否有任何節點（向後兼容）
            if node_count == 0:
                result = session.run("MATCH (n) RETURN count(n) as total_count")
                total_count = result.single()["total_count"]
                if total_count > 0:
                    return True

        driver.close()
        return node_count > 0

    except Exception:
        return False


async def verify_deletion_complete(workspace: str) -> bool:
    """驗證刪除是否完成"""
    print(f"🔍 驗證刪除完成狀態 - 命名空間: {workspace}")

    # 檢查 Qdrant 數據是否已清除
    has_qdrant = await has_qdrant_data(workspace)
    if has_qdrant:
        print(f"   ❌ Qdrant 數據未完全清除")
        return False
    else:
        print(f"   ✅ Qdrant 數據已清除")

    # 檢查 Neo4j 數據是否已清除
    has_neo4j = await has_neo4j_data(workspace)
    if has_neo4j:
        print(f"   ❌ Neo4j 數據未完全清除")
        return False
    else:
        print(f"   ✅ Neo4j 數據已清除")

    print(f"   ✅ 刪除驗證完成")
    return True


def get_data_status_summary(company_id: int) -> Dict[str, Any]:
    """獲取數據狀態摘要"""
    workspace = get_company_workspace(company_id)

    return {
        "company_id": company_id,
        "workspace": workspace,
        "timestamp": "pending_check",
        "qdrant_status": "pending",
        "neo4j_status": "pending",
        "overall_status": "pending",
    }
