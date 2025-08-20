"""
RAG-Anything 數據庫管理
"""

import os
from typing import Dict, Any, Optional
from .rag_config import RAGConfig


class DatabaseManager:
    """數據庫連接和狀態管理"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
    
    async def test_qdrant_connection(self) -> Dict[str, Any]:
        """測試 Qdrant 連接"""
        try:
            from qdrant_client import QdrantClient
            
            qdrant_client = QdrantClient(
                host=self.config.qdrant_host,
                port=self.config.qdrant_port,
            )
            collections = qdrant_client.get_collections()
            
            result = {
                "status": "success",
                "collections_count": len(collections.collections),
                "collections": []
            }
            
            for collection in collections.collections:
                try:
                    info = qdrant_client.get_collection(collection.name)
                    result["collections"].append({
                        "name": collection.name,
                        "points_count": info.points_count
                    })
                except Exception as e:
                    result["collections"].append({
                        "name": collection.name,
                        "error": str(e)
                    })
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Qdrant 連接失敗: {e}"
            }
    
    async def test_neo4j_connection(self) -> Dict[str, Any]:
        """測試 Neo4j 連接"""
        try:
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_username, self.config.neo4j_password),
            )
            
            with driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = result.single()["node_count"]
            
            driver.close()
            
            return {
                "status": "success",
                "node_count": node_count
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Neo4j 連接失敗: {e}"
            }
    
    async def check_database_status(self, company_id: str = None) -> Dict[str, Any]:
        """檢查數據庫狀態"""
        print("🔍 檢查數據庫連接狀態...")
        
        # 測試 Qdrant
        print("📊 測試 Qdrant 連接...")
        qdrant_result = await self.test_qdrant_connection()
        if qdrant_result["status"] == "success":
            print(f"✅ Qdrant 連接成功，集合數量: {qdrant_result['collections_count']}")
            for collection in qdrant_result["collections"]:
                if "error" not in collection:
                    print(f"   📦 {collection['name']}: {collection['points_count']} 個向量點")
                else:
                    print(f"   ❌ {collection['name']}: {collection['error']}")
        else:
            print(f"❌ {qdrant_result['message']}")
        
        # 測試 Neo4j
        print("🔗 測試 Neo4j 連接...")
        neo4j_result = await self.test_neo4j_connection()
        if neo4j_result["status"] == "success":
            print(f"✅ Neo4j 連接成功，總節點數: {neo4j_result['node_count']}")
        else:
            print(f"❌ {neo4j_result['message']}")
        
        return {
            "qdrant": qdrant_result,
            "neo4j": neo4j_result
        }
    
    async def check_company_data_status(self, company_id: str) -> Dict[str, Any]:
        """檢查特定公司的數據狀態"""
        company_workspace = self.config.get_company_workspace(company_id)
        
        # 檢查 Qdrant 中的公司數據
        qdrant_status = await self._check_qdrant_company_data(company_workspace)
        
        # 檢查 Neo4j 中的公司數據  
        neo4j_status = await self._check_neo4j_company_data(company_workspace)
        
        return {
            "company_id": company_id,
            "workspace": company_workspace,
            "qdrant": qdrant_status,
            "neo4j": neo4j_status
        }
    
    async def _check_qdrant_company_data(self, company_workspace: str) -> Dict[str, Any]:
        """檢查 Qdrant 中的公司數據"""
        try:
            from qdrant_client import QdrantClient
            
            qdrant_client = QdrantClient(
                host=self.config.qdrant_host,
                port=self.config.qdrant_port,
            )
            
            collections = qdrant_client.get_collections()
            workspace_collections = [
                c for c in collections.collections if company_workspace in c.name
            ]
            
            total_points = 0
            collection_details = []
            
            for collection in workspace_collections:
                try:
                    info = qdrant_client.get_collection(collection.name)
                    points_count = info.points_count
                    total_points += points_count
                    collection_details.append({
                        "name": collection.name,
                        "points_count": points_count
                    })
                except Exception as e:
                    collection_details.append({
                        "name": collection.name,
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "total_collections": len(workspace_collections),
                "total_points": total_points,
                "collections": collection_details
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _check_neo4j_company_data(self, company_workspace: str) -> Dict[str, Any]:
        """檢查 Neo4j 中的公司數據"""
        try:
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_username, self.config.neo4j_password),
            )
            
            with driver.session() as session:
                # 檢查公司節點總數
                result = session.run(
                    "MATCH (n) WHERE n.workspace = $workspace RETURN count(n) as node_count",
                    workspace=company_workspace,
                )
                node_count = result.single()["node_count"]
                
                # 檢查節點類型分布
                result = session.run(
                    """
                    MATCH (n) 
                    WHERE n.workspace = $workspace 
                    RETURN labels(n) as node_labels, count(n) as count
                    """,
                    workspace=company_workspace,
                )
                
                node_types = []
                for record in result:
                    labels = record["node_labels"]
                    count = record["count"]
                    node_types.append({
                        "labels": labels,
                        "count": count
                    })
            
            driver.close()
            
            return {
                "status": "success",
                "total_nodes": node_count,
                "node_types": node_types
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def delete_company_data(self, company_id: str) -> Dict[str, Any]:
        """刪除公司的所有數據"""
        company_workspace = self.config.get_company_workspace(company_id)
        
        print(f"🗑️  開始刪除公司 {company_id} 的所有數據...")
        print(f"   命名空間: {company_workspace}")
        
        # 從 Qdrant 刪除
        qdrant_result = await self._delete_qdrant_company_data(company_workspace)
        
        # 從 Neo4j 刪除
        neo4j_result = await self._delete_neo4j_company_data(company_workspace)
        
        return {
            "company_id": company_id,
            "workspace": company_workspace,
            "qdrant_deletion": qdrant_result,
            "neo4j_deletion": neo4j_result
        }
    
    async def _delete_qdrant_company_data(self, company_workspace: str) -> Dict[str, Any]:
        """從 Qdrant 刪除公司數據"""
        try:
            from qdrant_client import QdrantClient
            
            qdrant_client = QdrantClient(
                host=self.config.qdrant_host,
                port=self.config.qdrant_port,
            )
            
            collections = qdrant_client.get_collections()
            workspace_collections = [
                c for c in collections.collections if company_workspace in c.name
            ]
            
            deleted_collections = 0
            total_deleted_points = 0
            
            for collection in workspace_collections:
                try:
                    info = qdrant_client.get_collection(collection.name)
                    points_count = info.points_count
                    
                    qdrant_client.delete_collection(collection.name)
                    deleted_collections += 1
                    total_deleted_points += points_count
                    
                    print(f"   ✅ 刪除 Qdrant 集合: {collection.name} ({points_count} 點)")
                    
                except Exception as e:
                    print(f"   ❌ 刪除集合 {collection.name} 失敗: {e}")
            
            return {
                "status": "success",
                "deleted_collections": deleted_collections,
                "deleted_points": total_deleted_points
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _delete_neo4j_company_data(self, company_workspace: str) -> Dict[str, Any]:
        """從 Neo4j 刪除公司數據"""
        try:
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_username, self.config.neo4j_password),
            )
            
            with driver.session() as session:
                # 刪除所有公司節點
                result = session.run(
                    """
                    MATCH (n)
                    WHERE n.workspace = $workspace
                    DETACH DELETE n
                    RETURN count(n) as deleted_count
                    """,
                    workspace=company_workspace,
                )
                
                deleted_count = result.single()["deleted_count"]
                print(f"   ✅ 刪除 Neo4j 節點: {deleted_count} 個")
            
            driver.close()
            
            return {
                "status": "success",
                "deleted_nodes": deleted_count
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }