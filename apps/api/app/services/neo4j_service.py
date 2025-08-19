"""
Neo4j 知識圖譜服務
提供多租戶知識圖譜建構、存儲和查詢功能
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class Neo4jService:
    """Neo4j 知識圖譜服務類"""

    def __init__(self):
        self.driver = None
        self.initialized = False

        # Neo4j 連接配置
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "linerag123")

    async def initialize(self):
        """初始化 Neo4j 連接"""
        if self.initialized:
            return

        try:
            # 建立異步驅動程式
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60,
            )

            # 測試連接
            await self.verify_connectivity()

            # 建立索引和約束
            await self.create_indexes_and_constraints()

            self.initialized = True
            logger.info("✅ Neo4j service initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Neo4j service: {e}")
            raise

    async def verify_connectivity(self):
        """驗證 Neo4j 連接"""
        async with self.driver.session() as session:
            result = await session.run("RETURN 1 as test")
            record = await result.single()
            if record["test"] != 1:
                raise Exception("Neo4j connectivity test failed")

    async def create_indexes_and_constraints(self):
        """建立索引和約束"""
        async with self.driver.session() as session:
            # 建立唯一約束和索引
            constraints_and_indexes = [
                # 實體約束
                "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT entity_company_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.company_id IS NOT NULL",
                # 文檔約束
                "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT document_company_id IF NOT EXISTS FOR (d:Document) REQUIRE d.company_id IS NOT NULL",
                # 索引
                "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                "CREATE INDEX entity_company_index IF NOT EXISTS FOR (e:Entity) ON (e.company_id)",
                "CREATE INDEX document_company_index IF NOT EXISTS FOR (d:Document) ON (d.company_id)",
            ]

            for constraint in constraints_and_indexes:
                try:
                    await session.run(constraint)
                except Exception as e:
                    # 約束可能已存在，記錄但不中斷
                    logger.debug(f"Constraint/Index creation note: {e}")

    async def create_entity(self, company_id: int, entity_data: Dict[str, Any]) -> str:
        """建立實體節點"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            query = """
            MERGE (e:Entity {id: $entity_id, company_id: $company_id})
            SET e.name = $name,
                e.type = $type,
                e.description = $description,
                e.properties = $properties,
                e.created_at = datetime(),
                e.updated_at = datetime()
            RETURN e.id as entity_id
            """

            result = await session.run(
                query,
                {
                    "entity_id": entity_data.get("id"),
                    "company_id": company_id,
                    "name": entity_data.get("name"),
                    "type": entity_data.get("type"),
                    "description": entity_data.get("description", ""),
                    "properties": entity_data.get("properties", {}),
                },
            )

            record = await result.single()
            return record["entity_id"] if record else None

    async def create_relationship(
        self,
        company_id: int,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Dict[str, Any] = None,
    ) -> bool:
        """建立實體關係"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            query = """
            MATCH (source:Entity {id: $source_id, company_id: $company_id})
            MATCH (target:Entity {id: $target_id, company_id: $company_id})
            MERGE (source)-[r:RELATES_TO {type: $rel_type}]->(target)
            SET r.properties = $properties,
                r.created_at = datetime(),
                r.updated_at = datetime()
            RETURN r
            """

            result = await session.run(
                query,
                {
                    "source_id": source_id,
                    "target_id": target_id,
                    "company_id": company_id,
                    "rel_type": relationship_type,
                    "properties": properties or {},
                },
            )

            return await result.single() is not None

    async def create_document_node(
        self, company_id: int, document_data: Dict[str, Any]
    ) -> str:
        """建立文檔節點"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            query = """
            MERGE (d:Document {id: $doc_id, company_id: $company_id})
            SET d.filename = $filename,
                d.file_path = $file_path,
                d.file_type = $file_type,
                d.file_size = $file_size,
                d.metadata = $metadata,
                d.created_at = datetime(),
                d.updated_at = datetime()
            RETURN d.id as document_id
            """

            result = await session.run(
                query,
                {
                    "doc_id": document_data.get("id"),
                    "company_id": company_id,
                    "filename": document_data.get("filename"),
                    "file_path": document_data.get("file_path"),
                    "file_type": document_data.get("file_type"),
                    "file_size": document_data.get("file_size", 0),
                    "metadata": document_data.get("metadata", {}),
                },
            )

            record = await result.single()
            return record["document_id"] if record else None

    async def link_entity_to_document(
        self, company_id: int, entity_id: str, document_id: str
    ) -> bool:
        """連結實體到文檔"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            query = """
            MATCH (e:Entity {id: $entity_id, company_id: $company_id})
            MATCH (d:Document {id: $document_id, company_id: $company_id})
            MERGE (e)-[r:MENTIONED_IN]->(d)
            SET r.created_at = datetime()
            RETURN r
            """

            result = await session.run(
                query,
                {
                    "entity_id": entity_id,
                    "document_id": document_id,
                    "company_id": company_id,
                },
            )

            return await result.single() is not None

    async def query_related_entities(
        self, company_id: int, entity_id: str, max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """查詢相關實體"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            query = """
            MATCH (start:Entity {id: $entity_id, company_id: $company_id})
            MATCH (start)-[r*1..$max_depth]-(related:Entity)
            WHERE related.company_id = $company_id
            RETURN DISTINCT related.id as id, 
                   related.name as name, 
                   related.type as type,
                   related.description as description,
                   length(r) as distance
            ORDER BY distance, related.name
            LIMIT 50
            """

            result = await session.run(
                query,
                {
                    "entity_id": entity_id,
                    "company_id": company_id,
                    "max_depth": max_depth,
                },
            )

            entities = []
            async for record in result:
                entities.append(
                    {
                        "id": record["id"],
                        "name": record["name"],
                        "type": record["type"],
                        "description": record["description"],
                        "distance": record["distance"],
                    }
                )

            return entities

    async def search_entities(
        self,
        company_id: int,
        search_term: str,
        entity_type: str = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """搜尋實體"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            # 建構查詢條件
            where_conditions = ["e.company_id = $company_id"]
            params = {
                "company_id": company_id,
                "search_term": search_term,
                "limit": limit,
            }

            if entity_type:
                where_conditions.append("e.type = $entity_type")
                params["entity_type"] = entity_type

            # 使用全文搜尋或模糊匹配
            where_conditions.append(
                "(e.name CONTAINS $search_term OR e.description CONTAINS $search_term)"
            )

            query = f"""
            MATCH (e:Entity)
            WHERE {" AND ".join(where_conditions)}
            RETURN e.id as id, 
                   e.name as name, 
                   e.type as type,
                   e.description as description,
                   e.properties as properties
            ORDER BY e.name
            LIMIT $limit
            """

            result = await session.run(query, params)

            entities = []
            async for record in result:
                entities.append(
                    {
                        "id": record["id"],
                        "name": record["name"],
                        "type": record["type"],
                        "description": record["description"],
                        "properties": record["properties"],
                    }
                )

            return entities

    async def get_company_graph_stats(self, company_id: int) -> Dict[str, Any]:
        """取得公司圖譜統計"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            query = """
            MATCH (e:Entity {company_id: $company_id})
            OPTIONAL MATCH (d:Document {company_id: $company_id})
            OPTIONAL MATCH (e1:Entity {company_id: $company_id})-[r]-(e2:Entity {company_id: $company_id})
            RETURN count(DISTINCT e) as entity_count,
                   count(DISTINCT d) as document_count,
                   count(DISTINCT r) as relationship_count
            """

            result = await session.run(query, {"company_id": company_id})
            record = await result.single()

            return {
                "entity_count": record["entity_count"] if record else 0,
                "document_count": record["document_count"] if record else 0,
                "relationship_count": record["relationship_count"] if record else 0,
            }

    async def delete_company_data(self, company_id: int) -> bool:
        """刪除公司所有圖譜資料"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            # 刪除所有該公司的節點和關係
            query = """
            MATCH (n {company_id: $company_id})
            DETACH DELETE n
            """

            await session.run(query, {"company_id": company_id})
            return True

    async def close(self):
        """關閉 Neo4j 連接"""
        if self.driver:
            await self.driver.close()
            self.initialized = False


# 全域服務實例
_neo4j_service = None


def get_neo4j_service() -> Neo4jService:
    """取得 Neo4j 服務實例"""
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
    return _neo4j_service
