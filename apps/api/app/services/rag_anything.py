"""
RAG-Anything 服務整合 - 重構版本
提供多模態文檔處理和查詢功能
"""

import os
from typing import List, Dict, Any
from pathlib import Path

from raganything import RAGAnything
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

from .rag_config import RAGConfig
from .rag_database_manager import DatabaseManager
from .rag_document_processor import DocumentProcessor
from .rag_query_handler import QueryHandler
from .rag_knowledge_graph import KnowledgeGraphManager
from app.utils.namespace import AsyncNamespaceContext
from app.utils.data_validator import (
    verify_query_data_exists,
    verify_document_processing,
)

from dotenv import load_dotenv

load_dotenv()


class RAGAnythingService:
    """RAG-Anything 服務類 - 重構版本"""

    def __init__(self):
        # 核心組件
        self.config = RAGConfig()
        self.db_manager = DatabaseManager(self.config)

        # RAG 實例
        self.rag_instance = None

        # 功能模組
        self.document_processor = None
        self.query_handler = None
        self.knowledge_graph_manager = None

        # 狀態
        self.initialized = False

    async def initialize(self, company_id: str = None):
        """初始化 RAG-Anything 系統"""
        if self.initialized:
            return

        try:
            print("🔄 開始初始化 RAG-Anything 服務...")

            # 更新配置
            if company_id:
                self.config.company_id = company_id

            # 打印配置摘要
            self.config.print_config_summary()

            # 確保工作目錄存在
            self.config.ensure_working_dir()

            # 設置環境變數（如果有 company_id）
            if company_id:
                self._setup_environment()

            # 注意：不在這裡創建 RAG-Anything 實例
            # 實例將在每次處理時動態創建以使用正確的命名空間

            # 初始化數據庫管理器
            self.db_manager = DatabaseManager(self.config)

            # 初始化功能模組
            self._initialize_modules()

            # 測試數據庫連接
            await self.db_manager.check_database_status()

            self.initialized = True
            print("✅ RAG-Anything 服務初始化完成")

        except Exception as e:
            print(f"❌ RAG-Anything 服務初始化失敗: {e}")
            raise

    def _setup_environment(self):
        """設置環境變數"""
        print("🔧 設置環境變數...")

        # 設置 Qdrant 環境變數
        os.environ["QDRANT_URL"] = self.config.qdrant_url

        if self.config.company_id:
            company_workspace = self.config.get_company_workspace()
            os.environ["QDRANT_WORKSPACE"] = company_workspace
            os.environ["NEO4J_WORKSPACE"] = company_workspace

        print(f"   📊 Qdrant URL: {self.config.qdrant_url}")
        print(f"   🏷️  工作空間: {os.environ.get('QDRANT_WORKSPACE', 'default')}")

    async def _create_lightrag_instance(self):
        """創建 LightRAG 實例"""
        print("🔄 創建 LightRAG 實例...")

        from lightrag import LightRAG

        # 獲取配置
        llm_config = self.config.get_llm_config()
        vision_config = self.config.get_vision_model_config()
        embedding_config = self.config.get_embedding_config()

        # 定義 LLM 模型函數
        def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
            return openai_complete_if_cache(
                llm_config["model"],
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=llm_config["api_key"],
                base_url=llm_config["base_url"],
                **kwargs,
            )

        # 定義視覺模型函數
        def vision_model_func(
            prompt,
            system_prompt=None,
            history_messages=[],
            image_data=None,
            **kwargs,
        ):
            if image_data:
                return openai_complete_if_cache(
                    vision_config["model"],
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=[
                        (
                            {"role": "system", "content": system_prompt}
                            if system_prompt
                            else None
                        ),
                        (
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_data}"
                                        },
                                    },
                                ],
                            }
                            if image_data
                            else {"role": "user", "content": prompt}
                        ),
                    ],
                    api_key=vision_config["api_key"],
                    base_url=vision_config["base_url"],
                    **kwargs,
                )
            else:
                return llm_model_func(prompt, system_prompt, history_messages, **kwargs)

        # 定義嵌入函數
        embedding_func = EmbeddingFunc(
            embedding_dim=embedding_config["embedding_dim"],
            max_token_size=embedding_config["max_token_size"],
            func=lambda texts: openai_embed(
                texts,
                model=embedding_config["model"],
                api_key=embedding_config["api_key"],
                base_url=embedding_config["base_url"],
            ),
        )

        # 創建 LightRAG 實例
        lightrag_instance = LightRAG(
            working_dir=self.config.working_dir,
            llm_model_func=llm_model_func,
            embedding_func=embedding_func,
            vector_storage="QdrantVectorDBStorage",
            graph_storage="Neo4JStorage",
        )

        # 初始化存儲
        print("🔄 初始化 LightRAG 存儲...")
        await lightrag_instance.initialize_storages()
        print("✅ LightRAG 存儲初始化完成")

        return lightrag_instance

    async def _create_rag_instance(self, lightrag_instance):
        """創建 RAG-Anything 實例 - 使用 test.py 成功模式"""
        print("🔄 創建 RAG-Anything 實例...")

        from raganything import RAGAnythingConfig

        # 獲取配置
        llm_config = self.config.get_llm_config()
        embedding_config = self.config.get_embedding_config()
        vision_config = self.config.get_vision_model_config()

        # 創建 RAGAnythingConfig (像 test.py 一樣)
        rag_config = RAGAnythingConfig(
            working_dir=self.config.working_dir,
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )

        print(f"🔧 RAG-Anything 工作目錄: {self.config.working_dir}")
        print(f"🔧 當前命名空間環境變數:")
        print(f"   QDRANT_WORKSPACE: {os.environ.get('QDRANT_WORKSPACE', 'default')}")
        print(f"   NEO4J_WORKSPACE: {os.environ.get('NEO4J_WORKSPACE', 'default')}")

        # 定義 LLM 模型函數 (像 test.py 一樣)
        def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
            return openai_complete_if_cache(
                llm_config["model"],
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=llm_config["api_key"],
                base_url=llm_config["base_url"],
                **kwargs,
            )

        # 定義視覺模型函數 (像 test.py 一樣)
        def vision_model_func(
            prompt,
            system_prompt=None,
            history_messages=[],
            image_data=None,
            messages=None,
            **kwargs,
        ):
            # 如果提供了messages格式（用於多模態VLM增強查詢），直接使用
            if messages:
                return openai_complete_if_cache(
                    vision_config["model"],
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=messages,
                    api_key=vision_config["api_key"],
                    base_url=vision_config["base_url"],
                    **kwargs,
                )
            # 傳統單圖片格式
            elif image_data:
                return openai_complete_if_cache(
                    vision_config["model"],
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=[
                        (
                            {"role": "system", "content": system_prompt}
                            if system_prompt
                            else None
                        ),
                        (
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_data}"
                                        },
                                    },
                                ],
                            }
                            if image_data
                            else {"role": "user", "content": prompt}
                        ),
                    ],
                    api_key=vision_config["api_key"],
                    base_url=vision_config["base_url"],
                    **kwargs,
                )
            # 純文本格式
            else:
                return llm_model_func(prompt, system_prompt, history_messages, **kwargs)

        # 定義嵌入函數 (像 test.py 一樣)
        embedding_func = EmbeddingFunc(
            embedding_dim=embedding_config["embedding_dim"],
            max_token_size=embedding_config["max_token_size"],
            func=lambda texts: openai_embed(
                texts,
                model=embedding_config["model"],
                api_key=embedding_config["api_key"],
                base_url=embedding_config["base_url"],
            ),
        )

        # 創建 RAG-Anything 實例 (像 test.py 一樣，使用配置而非現有實例)
        rag_instance = RAGAnything(
            config=rag_config,
            llm_model_func=llm_model_func,
            vision_model_func=vision_model_func,
            embedding_func=embedding_func,
        )

        print("✅ RAG-Anything 實例創建完成")
        return rag_instance

    async def get_rag_instance_for_company(self, company_id: str):
        """為特定公司動態創建 RAG-Anything 實例（在正確的命名空間下）"""
        print(f"🔄 為公司 {company_id} 創建 RAG-Anything 實例...")

        # 更新配置
        original_company_id = self.config.company_id
        self.config.company_id = company_id

        try:
            # 設置命名空間環境變數
            company_workspace = self.config.set_company_namespace(company_id)
            print(f"   📌 設置命名空間: {company_workspace}")

            # 確保工作目錄存在
            self.config.ensure_working_dir()

            # 在正確的命名空間下創建 RAG-Anything 實例
            rag_instance = await self._create_rag_instance_direct()

            print(f"✅ 公司 {company_id} 的 RAG-Anything 實例創建成功")
            return rag_instance

        except Exception as e:
            print(f"❌ 公司 {company_id} 的 RAG-Anything 實例創建失敗: {e}")
            raise
        finally:
            # 恢復原始配置
            self.config.company_id = original_company_id

    async def _create_rag_instance_direct(self):
        """直接創建 RAG-Anything 實例（不依賴 lightrag_instance 參數）"""
        print("🔄 創建 RAG-Anything 實例...")

        from raganything import RAGAnythingConfig

        # 獲取配置
        llm_config = self.config.get_llm_config()
        embedding_config = self.config.get_embedding_config()
        vision_config = self.config.get_vision_model_config()

        # 創建 RAGAnythingConfig (像 test.py 一樣)
        rag_config = RAGAnythingConfig(
            working_dir=self.config.working_dir,
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )

        print(f"🔧 RAG-Anything 工作目錄: {self.config.working_dir}")
        print(f"🔧 當前命名空間環境變數:")
        print(f"   QDRANT_WORKSPACE: {os.environ.get('QDRANT_WORKSPACE', 'default')}")
        print(f"   NEO4J_WORKSPACE: {os.environ.get('NEO4J_WORKSPACE', 'default')}")

        # 定義 LLM 模型函數 (像 test.py 一樣)
        def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
            return openai_complete_if_cache(
                llm_config["model"],
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=llm_config["api_key"],
                base_url=llm_config["base_url"],
                **kwargs,
            )

        # 定義視覺模型函數 (像 test.py 一樣)
        def vision_model_func(
            prompt,
            system_prompt=None,
            history_messages=[],
            image_data=None,
            messages=None,
            **kwargs,
        ):
            # 如果提供了messages格式（用於多模態VLM增強查詢），直接使用
            if messages:
                return openai_complete_if_cache(
                    vision_config["model"],
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=messages,
                    api_key=vision_config["api_key"],
                    base_url=vision_config["base_url"],
                    **kwargs,
                )
            # 傳統單圖片格式
            elif image_data:
                return openai_complete_if_cache(
                    vision_config["model"],
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=[
                        (
                            {"role": "system", "content": system_prompt}
                            if system_prompt
                            else None
                        ),
                        (
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_data}"
                                        },
                                    },
                                ],
                            }
                            if image_data
                            else {"role": "user", "content": prompt}
                        ),
                    ],
                    api_key=vision_config["api_key"],
                    base_url=vision_config["base_url"],
                    **kwargs,
                )
            # 純文本格式
            else:
                return llm_model_func(prompt, system_prompt, history_messages, **kwargs)

        # 定義嵌入函數 (像 test.py 一樣)
        embedding_func = EmbeddingFunc(
            embedding_dim=embedding_config["embedding_dim"],
            max_token_size=embedding_config["max_token_size"],
            func=lambda texts: openai_embed(
                texts,
                model=embedding_config["model"],
                api_key=embedding_config["api_key"],
                base_url=embedding_config["base_url"],
            ),
        )

        # 創建 RAG-Anything 實例 (像 test.py 一樣，使用配置而非現有實例)
        rag_instance = RAGAnything(
            config=rag_config,
            llm_model_func=llm_model_func,
            vision_model_func=vision_model_func,
            embedding_func=embedding_func,
        )

        print("✅ RAG-Anything 實例創建完成")
        return rag_instance

    def _initialize_modules(self):
        """初始化功能模組"""
        print("🔄 初始化功能模組...")

        self.document_processor = DocumentProcessor(
            self, self.config, self.db_manager  # 傳遞 self (服務引用)
        )

        # 初始化查詢處理器 - 核心 RAG 功能
        from .rag_query_handler import QueryHandler

        self.query_handler = QueryHandler(
            self, self.config, self.db_manager  # 傳遞 self (服務引用)
        )

        # 初始化知識圖譜管理器 - RAG 查詢可能需要
        from .rag_knowledge_graph import KnowledgeGraphManager

        self.knowledge_graph_manager = KnowledgeGraphManager(
            self, self.config  # 傳遞 self (服務引用)
        )

        print("✅ 功能模組初始化完成")

    # 文檔處理相關方法
    async def process_document(
        self, file_path: str, company_id: str, output_dir: str = "./output"
    ) -> Dict[str, Any]:
        """處理單個文檔"""
        if not self.initialized:
            await self.initialize(company_id)
        # 確保document_processor使用正確的company_id配置
        self.config.company_id = company_id
        return await self.document_processor.process_document(
            file_path, company_id, output_dir
        )

    async def process_folder(
        self, folder_path: str, company_id: str, output_dir: str = "./output"
    ) -> Dict[str, Any]:
        """批量處理文檔資料夾"""
        if not self.initialized:
            await self.initialize()
        return await self.document_processor.process_folder(
            folder_path, company_id, output_dir
        )

    async def insert_content_list(
        self, content_list: List[Dict], file_path: str, company_id: str
    ) -> Dict[str, Any]:
        """直接插入內容列表"""
        if not self.initialized:
            await self.initialize()
        return await self.document_processor.insert_content_list(
            content_list, file_path, company_id
        )

    async def delete_document(
        self, document_id: str, company_id: str
    ) -> Dict[str, Any]:
        """刪除文檔"""
        if not self.initialized:
            await self.initialize()
        return await self.document_processor.delete_document(document_id, company_id)

    # 查詢相關方法
    async def query_text(
        self, query: str, mode: str = "hybrid", company_id: str = None
    ) -> str:
        """純文本查詢"""
        if not self.initialized:
            await self.initialize()
        return await self.query_handler.query_text(query, mode, company_id)

    async def query_multimodal(
        self,
        query: str,
        multimodal_content: List[Dict],
        mode: str = "hybrid",
        company_id: str = None,
    ) -> str:
        """多模態查詢"""
        if not self.initialized:
            await self.initialize()
        return await self.query_handler.query_multimodal(
            query, multimodal_content, mode, company_id
        )

    # 知識圖譜相關方法
    async def get_entity_details(
        self, company_id: int, entity_id: str
    ) -> Dict[str, Any]:
        """取得實體詳細資訊"""
        if not self.initialized:
            await self.initialize()
        return await self.knowledge_graph_manager.get_entity_details(
            company_id, entity_id
        )

    async def search_entities_by_type(
        self, company_id: int, entity_type: str, limit: int = 20
    ) -> Dict[str, Any]:
        """按類型搜尋實體"""
        if not self.initialized:
            await self.initialize()
        return await self.knowledge_graph_manager.search_entities_by_type(
            company_id, entity_type, limit
        )

    async def get_knowledge_graph_visualization(
        self, company_id: int, center_entity_id: str = None, max_nodes: int = 50
    ) -> Dict[str, Any]:
        """取得知識圖譜視覺化資料"""
        if not self.initialized:
            await self.initialize()
        return await self.knowledge_graph_manager.get_knowledge_graph_visualization(
            company_id, center_entity_id, max_nodes
        )

    async def create_knowledge_graph_from_document(
        self, file_path: str, company_id: int, document_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """從文檔建立知識圖譜"""
        if not self.initialized:
            await self.initialize()
        return await self.knowledge_graph_manager.create_knowledge_graph_from_document(
            file_path, company_id, document_metadata
        )

    async def query_knowledge_graph(
        self, company_id: int, entity_name: str, max_depth: int = 2
    ) -> Dict[str, Any]:
        """查詢知識圖譜"""
        if not self.initialized:
            await self.initialize()
        return await self.knowledge_graph_manager.query_knowledge_graph(
            company_id, entity_name, max_depth
        )

    async def get_graph_stats(self, company_id: int) -> Dict[str, Any]:
        """取得知識圖譜統計"""
        if not self.initialized:
            await self.initialize()
        return await self.knowledge_graph_manager.get_graph_stats(company_id)

    # 系統狀態相關方法
    def get_status(self) -> Dict[str, Any]:
        """取得服務狀態"""
        return {
            "initialized": self.initialized,
            "rag_instance": self.rag_instance is not None,
            "document_processor": self.document_processor is not None,
            "query_handler": self.query_handler is not None,
            "knowledge_graph_manager": self.knowledge_graph_manager is not None,
            "service": "RAG-Anything (Refactored)",
            "modules_loaded": [
                "DocumentProcessor",
                "QueryHandler",
                "KnowledgeGraphManager",
                "DatabaseManager",
                "RAGConfig",
            ],
        }

    def get_api_stats(self) -> Dict[str, Any]:
        """取得 API 使用統計"""
        if self.query_handler:
            return self.query_handler.get_api_stats()
        return {
            "total_calls": 0,
            "error_count": 0,
            "success_count": 0,
            "success_rate_percent": 0,
            "service_health": "not_initialized",
        }


# 全域實例
_rag_service = None


def get_rag_service() -> RAGAnythingService:
    """取得 RAG-Anything 服務實例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGAnythingService()
    return _rag_service
