"""
RAG-Anything 知識圖譜管理器
"""

import json
import re
from typing import Dict, Any, List
from pathlib import Path

from app.services.neo4j_service import get_neo4j_service
from .rag_config import RAGConfig


class KnowledgeGraphManager:
    """知識圖譜管理器"""

    def __init__(self, rag_service, config: RAGConfig):
        self.rag_service = rag_service  # 持有 RAG 服務引用而不是實例
        self.config = config
        self.neo4j_service = None

    async def initialize(self):
        """初始化 Neo4j 服務"""
        if not self.neo4j_service:
            self.neo4j_service = get_neo4j_service()
            await self.neo4j_service.initialize()

    async def get_entity_details(
        self, company_id: int, entity_id: str
    ) -> Dict[str, Any]:
        """取得實體詳細資訊"""
        await self.initialize()

        try:
            # 從 Neo4j 取得實體詳細資訊
            entities = await self.neo4j_service.search_entities(
                company_id=company_id, search_term=entity_id, limit=1
            )

            if not entities:
                return {"status": "error", "message": "Entity not found"}

            entity = entities[0]

            # 取得相關實體
            related_entities = await self.neo4j_service.query_related_entities(
                company_id=company_id, entity_id=entity_id, max_depth=2
            )

            return {
                "status": "success",
                "entity": entity,
                "related_entities": related_entities,
                "relationship_count": len(related_entities),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get entity details: {str(e)}",
            }

    async def search_entities_by_type(
        self, company_id: int, entity_type: str, limit: int = 20
    ) -> Dict[str, Any]:
        """按類型搜尋實體"""
        await self.initialize()

        try:
            entities = await self.neo4j_service.search_entities(
                company_id=company_id,
                search_term="",
                entity_type=entity_type,
                limit=limit,
            )

            return {
                "status": "success",
                "entity_type": entity_type,
                "entities": entities,
                "count": len(entities),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to search entities by type: {str(e)}",
            }

    async def get_knowledge_graph_visualization(
        self, company_id: int, center_entity_id: str = None, max_nodes: int = 50
    ) -> Dict[str, Any]:
        """取得知識圖譜視覺化資料"""
        await self.initialize()

        try:
            if center_entity_id:
                # 以特定實體為中心的圖譜
                related_entities = await self.neo4j_service.query_related_entities(
                    company_id=company_id, entity_id=center_entity_id, max_depth=2
                )

                # 取得中心實體
                center_entities = await self.neo4j_service.search_entities(
                    company_id=company_id, search_term=center_entity_id, limit=1
                )

                all_entities = center_entities + related_entities
            else:
                # 取得所有實體的子集
                all_entities = await self.neo4j_service.search_entities(
                    company_id=company_id, search_term="", limit=max_nodes
                )

            # 轉換為視覺化格式
            nodes = []
            for entity in all_entities[:max_nodes]:
                nodes.append(
                    {
                        "id": entity["id"],
                        "label": entity["name"],
                        "type": entity["type"],
                        "description": entity.get("description", ""),
                        "properties": entity.get("properties", {}),
                    }
                )

            # TODO: 實作邊的查詢
            edges = []

            return {
                "status": "success",
                "nodes": nodes,
                "edges": edges,
                "center_entity": center_entity_id,
                "total_nodes": len(nodes),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get visualization data: {str(e)}",
            }

    async def create_knowledge_graph_from_document(
        self, file_path: str, company_id: int, document_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """從文檔建立知識圖譜"""
        await self.initialize()

        try:
            # 建立文檔節點
            doc_id = (
                f"{company_id}_{Path(file_path).stem}_{document_metadata.get('id', '')}"
            )
            await self.neo4j_service.create_document_node(
                company_id=company_id,
                document_data={
                    "id": doc_id,
                    "filename": document_metadata.get("filename"),
                    "file_path": file_path,
                    "file_type": document_metadata.get("file_type"),
                    "file_size": document_metadata.get("file_size", 0),
                    "metadata": document_metadata,
                },
            )

            # 提取實體
            entities = await self._extract_entities_from_document(file_path, company_id)

            entity_ids = []
            for entity in entities:
                entity_id = await self.neo4j_service.create_entity(
                    company_id=company_id, entity_data=entity
                )
                if entity_id:
                    entity_ids.append(entity_id)
                    # 連結實體到文檔
                    await self.neo4j_service.link_entity_to_document(
                        company_id=company_id, entity_id=entity_id, document_id=doc_id
                    )

            # 提取關係
            relationships = await self._extract_relationships_from_entities(
                entities, company_id
            )

            relationship_count = 0
            for rel in relationships:
                success = await self.neo4j_service.create_relationship(
                    company_id=company_id,
                    source_id=rel["source_id"],
                    target_id=rel["target_id"],
                    relationship_type=rel["type"],
                    properties=rel.get("properties", {}),
                )
                if success:
                    relationship_count += 1

            return {
                "status": "success",
                "message": f"Knowledge graph created for document {file_path}",
                "document_id": doc_id,
                "entities_created": len(entity_ids),
                "relationships_created": relationship_count,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to create knowledge graph: {str(e)}",
                "file_path": file_path,
            }

    async def query_knowledge_graph(
        self, company_id: int, entity_name: str, max_depth: int = 2
    ) -> Dict[str, Any]:
        """查詢知識圖譜"""
        await self.initialize()

        try:
            # 搜尋實體
            entities = await self.neo4j_service.search_entities(
                company_id=company_id, search_term=entity_name, limit=10
            )

            if not entities:
                return {
                    "status": "success",
                    "message": "No entities found",
                    "entities": [],
                    "related_entities": [],
                }

            # 取得相關實體
            related_entities = []
            for entity in entities[:3]:  # 限制前3個實體
                related = await self.neo4j_service.query_related_entities(
                    company_id=company_id, entity_id=entity["id"], max_depth=max_depth
                )
                related_entities.extend(related)

            return {
                "status": "success",
                "message": f"Found {len(entities)} entities and {len(related_entities)} related entities",
                "entities": entities,
                "related_entities": related_entities,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to query knowledge graph: {str(e)}",
            }

    async def get_graph_stats(self, company_id: int) -> Dict[str, Any]:
        """取得知識圖譜統計"""
        await self.initialize()

        try:
            stats = await self.neo4j_service.get_company_graph_stats(company_id)
            return {"status": "success", "stats": stats}
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get graph stats: {str(e)}",
            }

    async def _extract_entities_from_document(
        self, file_path: str, company_id: int
    ) -> List[Dict[str, Any]]:
        """從文檔提取實體"""
        try:
            # 讀取文檔內容
            content = ""
            if file_path.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                # 對於其他格式，使用基本文件名作為內容
                content = f"Document: {Path(file_path).stem}"

            # 使用 LLM 進行實體提取
            if hasattr(self.rag_instance, "lightrag") and self.rag_instance.lightrag:
                entity_extraction_prompt = f"""
請從以下文檔內容中提取重要的實體，包括人名、地名、組織名、產品名、概念等。
請以 JSON 格式返回，每個實體包含 name, type, description 字段。

文檔內容：
{content[:2000]}  # 限制長度避免 token 過多

請返回 JSON 格式：
[
    {{"name": "實體名稱", "type": "實體類型", "description": "實體描述"}},
    ...
]
"""

                try:
                    llm_response = await self.rag_instance.lightrag.llm_model_func(
                        entity_extraction_prompt,
                        system_prompt="你是一個專業的實體提取助手，請準確識別文檔中的重要實體。",
                    )

                    # 解析 LLM 回應
                    json_match = re.search(r"\[.*\]", llm_response, re.DOTALL)
                    if json_match:
                        try:
                            extracted_entities = json.loads(json_match.group())
                            return self._format_entities(
                                extracted_entities, file_path, company_id
                            )
                        except json.JSONDecodeError:
                            pass

                except Exception as e:
                    print(f"LLM entity extraction failed: {e}")

            # 備用方案：創建基本文檔實體
            return self._create_fallback_entities(file_path, company_id)

        except Exception as e:
            print(f"Entity extraction failed: {e}")
            return self._create_fallback_entities(file_path, company_id)

    def _format_entities(
        self, extracted_entities: List[Dict], file_path: str, company_id: int
    ) -> List[Dict[str, Any]]:
        """格式化提取的實體"""
        entities = []
        filename = Path(file_path).stem

        for i, entity in enumerate(extracted_entities[:10]):  # 限制最多10個實體
            entity_id = f"{company_id}_{filename}_entity_{i+1}"
            entities.append(
                {
                    "id": entity_id,
                    "name": entity.get("name", f"Entity_{i+1}"),
                    "type": entity.get("type", "Unknown"),
                    "description": entity.get("description", ""),
                    "properties": {
                        "source_file": file_path,
                        "extraction_method": "llm",
                        "confidence": 0.8,
                    },
                }
            )

        # 添加文檔本身作為實體
        entities.append(
            {
                "id": f"{company_id}_{filename}_document",
                "name": filename,
                "type": "Document",
                "description": f"Document entity for {filename}",
                "properties": {
                    "source_file": file_path,
                    "extraction_method": "automatic",
                    "confidence": 1.0,
                },
            }
        )

        return entities

    def _create_fallback_entities(
        self, file_path: str, company_id: int
    ) -> List[Dict[str, Any]]:
        """創建備用實體"""
        filename = Path(file_path).stem
        return [
            {
                "id": f"{company_id}_{filename}_document",
                "name": filename,
                "type": "Document",
                "description": f"Document entity for {filename}",
                "properties": {
                    "source_file": file_path,
                    "extraction_method": "fallback",
                    "confidence": 0.5,
                },
            }
        ]

    async def _extract_relationships_from_entities(
        self, entities: List[Dict[str, Any]], company_id: int
    ) -> List[Dict[str, Any]]:
        """從實體提取關係"""
        try:
            if len(entities) < 2:
                return []

            relationships = []

            # 使用 LLM 進行關係提取
            if hasattr(self.rag_instance, "lightrag") and self.rag_instance.lightrag:
                entity_list = []
                for entity in entities:
                    entity_list.append(
                        f"- {entity['name']} ({entity['type']}): {entity['description']}"
                    )

                entity_text = "\n".join(entity_list)

                relationship_extraction_prompt = f"""
請分析以下實體之間可能存在的關係，並以 JSON 格式返回。

實體列表：
{entity_text}

請識別實體之間的關係，如：
- 包含關係 (contains)
- 相關關係 (related_to)
- 屬於關係 (belongs_to)
- 引用關係 (references)
- 依賴關係 (depends_on)

請返回 JSON 格式：
[
    {{"source": "實體1名稱", "target": "實體2名稱", "type": "關係類型", "description": "關係描述"}},
    ...
]
"""

                try:
                    llm_response = await self.rag_instance.lightrag.llm_model_func(
                        relationship_extraction_prompt,
                        system_prompt="你是一個專業的關係提取助手，請準確識別實體之間的語義關係。",
                    )

                    json_match = re.search(r"\[.*\]", llm_response, re.DOTALL)
                    if json_match:
                        try:
                            extracted_relationships = json.loads(json_match.group())
                            relationships.extend(
                                self._format_relationships(
                                    extracted_relationships, entities, company_id
                                )
                            )
                        except json.JSONDecodeError:
                            pass

                except Exception as e:
                    print(f"LLM relationship extraction failed: {e}")

            # 基於規則的關係提取（備用方案）
            relationships.extend(
                self._create_rule_based_relationships(entities, company_id)
            )

            return relationships

        except Exception as e:
            print(f"Relationship extraction failed: {e}")
            return []

    def _format_relationships(
        self, extracted_relationships: List[Dict], entities: List[Dict], company_id: int
    ) -> List[Dict[str, Any]]:
        """格式化提取的關係"""
        relationships = []

        # 建立實體名稱到 ID 的映射
        entity_name_to_id = {entity["name"]: entity["id"] for entity in entities}

        for i, rel in enumerate(extracted_relationships[:20]):  # 限制最多20個關係
            source_name = rel.get("source", "")
            target_name = rel.get("target", "")

            # 查找對應的實體 ID
            source_id = entity_name_to_id.get(source_name)
            target_id = entity_name_to_id.get(target_name)

            if source_id and target_id and source_id != target_id:
                relationships.append(
                    {
                        "source_id": source_id,
                        "target_id": target_id,
                        "type": rel.get("type", "related_to"),
                        "properties": {
                            "description": rel.get("description", ""),
                            "extraction_method": "llm",
                            "confidence": 0.7,
                            "company_id": company_id,
                        },
                    }
                )

        return relationships

    def _create_rule_based_relationships(
        self, entities: List[Dict[str, Any]], company_id: int
    ) -> List[Dict[str, Any]]:
        """創建基於規則的關係"""
        relationships = []

        # 為所有非文檔實體與文檔實體建立 "mentioned_in" 關係
        document_entities = [e for e in entities if e["type"] == "Document"]
        non_document_entities = [e for e in entities if e["type"] != "Document"]

        for doc_entity in document_entities:
            for other_entity in non_document_entities:
                relationships.append(
                    {
                        "source_id": other_entity["id"],
                        "target_id": doc_entity["id"],
                        "type": "mentioned_in",
                        "properties": {
                            "description": f"{other_entity['name']} is mentioned in {doc_entity['name']}",
                            "extraction_method": "rule_based",
                            "confidence": 0.6,
                            "company_id": company_id,
                        },
                    }
                )

        return relationships
