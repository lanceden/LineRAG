"""RAG-Anything 服務整合 - 重構版本
提供多模態文檔處理和查詢功能
使用獨立文件夾架構確保數據隔離
"""

import os
import json
import asyncio
import hashlib
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from .rag_config import RAGConfig
from .rag_database_manager import DatabaseManager
from app.utils.namespace import AsyncNamespaceContext
from app.utils.data_validator import verify_document_processing

# RAG-Anything imports
from raganything import RAGAnything, RAGAnythingConfig
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

from dotenv import load_dotenv

load_dotenv()


class RAGAnythingService:
    """RAG-Anything 服務類 - 重構版本，專注於獨立文件夾架構"""

    def __init__(self, company_id: str = None):
        """初始化 RAG-Anything 服務"""
        # 載入配置
        self.config = RAGConfig(company_id=company_id)

        # RAG-Anything 實例
        self.rag_instance = None
        self.rag_config = None

        # 服務狀態
        self.initialized = False
        self.company_id = company_id

        print(f"🏗️ RAG-Anything 服務初始化中... (公司 ID: {company_id})")

    async def initialize(self, company_id: str = None):
        """初始化 RAG-Anything 服務"""
        try:
            print("🚀 初始化 RAG-Anything 服務...")

            # 設置環境變數（如果有 company_id）
            if company_id:
                self.company_id = company_id
                self.config.company_id = company_id

            # 初始化數據庫管理器
            self.db_manager = DatabaseManager(self.config)

            # 測試數據庫連接
            await self.db_manager.check_database_status()

            # 初始化 RAG-Anything 配置
            await self._initialize_rag_anything()

            self.initialized = True
            print("✅ RAG-Anything 服務初始化完成")

        except Exception as e:
            print(f"❌ RAG-Anything 服務初始化失敗: {e}")
            raise

    async def _initialize_rag_anything(self):
        """初始化 RAG-Anything 實例"""
        try:
            # 獲取 API 配置
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")

            if not api_key:
                raise Exception("OPENAI_API_KEY 環境變數未設置")

            # 創建 RAG-Anything 配置 - 使用公司基礎目錄
            # 實際處理時會動態切換到各文檔的獨立文件夾
            company_base_dir = f"./rag_storage/company_{self.company_id}"
            Path(company_base_dir).mkdir(parents=True, exist_ok=True)
            
            self.rag_config = RAGAnythingConfig(
                working_dir=company_base_dir,
                parser="mineru",  # 使用 MinerU 解析器處理 PDF
                parse_method="auto",
                enable_image_processing=True,
                enable_table_processing=True,
                enable_equation_processing=True,
            )

            # 定義 LLM 模型函數
            def llm_model_func(
                prompt, system_prompt=None, history_messages=[], **kwargs
            ):
                return openai_complete_if_cache(
                    "gpt-4o-mini",
                    prompt,
                    system_prompt=system_prompt,
                    history_messages=history_messages,
                    api_key=api_key,
                    base_url=base_url,
                    **kwargs,
                )

            # 定義視覺模型函數（用於圖像處理）
            def vision_model_func(
                prompt,
                system_prompt=None,
                history_messages=[],
                image_data=None,
                messages=None,
                **kwargs,
            ):
                if messages:
                    return openai_complete_if_cache(
                        "gpt-4o",
                        "",
                        system_prompt=None,
                        history_messages=[],
                        messages=messages,
                        api_key=api_key,
                        base_url=base_url,
                        **kwargs,
                    )
                elif image_data:
                    return openai_complete_if_cache(
                        "gpt-4o",
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
                        api_key=api_key,
                        base_url=base_url,
                        **kwargs,
                    )
                else:
                    return llm_model_func(
                        prompt, system_prompt, history_messages, **kwargs
                    )

            # 定義嵌入函數
            embedding_func = EmbeddingFunc(
                embedding_dim=3072,
                max_token_size=8192,
                func=lambda texts: openai_embed(
                    texts,
                    model="text-embedding-3-large",
                    api_key=api_key,
                    base_url=base_url,
                ),
            )

            # 初始化 RAG-Anything 實例
            self.rag_instance = RAGAnything(
                config=self.rag_config,
                llm_model_func=llm_model_func,
                vision_model_func=vision_model_func,
                embedding_func=embedding_func,
            )

            print("✅ RAG-Anything 實例初始化完成")

        except Exception as e:
            print(f"❌ RAG-Anything 實例初始化失敗: {e}")
            raise

    async def process_document(
        self, file_path: str, company_id: int, output_dir: str = "./output"
    ) -> Dict[str, Any]:
        """處理單個文檔 - 使用 RAG-Anything 進行完整的多模態處理"""
        # 只在第一次調用時初始化
        if not self.initialized:
            await self.initialize(str(company_id))

        # 確保配置使用正確的company_id
        self.config.company_id = str(company_id)

        try:
            print(f"📄 開始處理文檔: {file_path} (公司: {company_id})")

            # 檢查文件是否存在
            if not Path(file_path).exists():
                raise Exception(f"文件不存在: {file_path}")

            # 創建文檔ID
            file_hash = hashlib.md5(
                f"{file_path}_{company_id}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            doc_id = f"doc-{file_hash}"

            # 創建獨立的文檔文件夾
            company_dir = Path(f"./rag_storage/company_{company_id}")
            doc_folder = company_dir / doc_id
            doc_folder.mkdir(parents=True, exist_ok=True)

            print(f"📁 創建文檔文件夾: {doc_folder}")

            # 使用 RAG-Anything 處理文檔
            print(f"🔄 使用 RAG-Anything 處理文檔內容...")

            start_time = datetime.now()

            # 臨時更新 RAG-Anything 實例的工作目錄為文檔特定目錄
            original_working_dir = self.rag_instance.config.working_dir
            self.rag_instance.config.working_dir = str(doc_folder)
            
            try:
                # 直接調用異步的process_document_complete方法
                await self.rag_instance.process_document_complete(
                    file_path=file_path, output_dir=str(doc_folder), parse_method="auto"
                )
            finally:
                # 恢復原始工作目錄
                self.rag_instance.config.working_dir = original_working_dir

            processing_time = (datetime.now() - start_time).total_seconds()

            # 檢查生成的存儲文件（使用 LightRAG 實際生成的文件名）
            storage_files = {
                "chunks_vdb": doc_folder / "kv_store_chunks_vdb.pkl",
                "entities_vdb": doc_folder / "kv_store_entities_vdb.pkl",
                "relationships_vdb": doc_folder / "kv_store_relationships_vdb.pkl",
                "text_chunks": doc_folder / "kv_store_text_chunks.json",
                "knowledge_graph": doc_folder / "kv_store_chunk_entity_relation_graph.pkl",
                "llm_cache": doc_folder / "kv_store_llm_response_cache.json",
                "full_docs": doc_folder / "kv_store_full_docs.json",
                "full_entities": doc_folder / "kv_store_full_entities.json",
                "full_relations": doc_folder / "kv_store_full_relations.json",
                "doc_status": doc_folder / "kv_store_doc_status.json",
            }

            # 統計生成的文件
            generated_files = []
            total_size = 0

            for file_name, file_path in storage_files.items():
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    generated_files.append(
                        {"name": file_name, "path": str(file_path), "size": file_size}
                    )
                    print(f"   ✅ 生成 {file_name}: {file_size} bytes")
                else:
                    print(f"   ⚠️ 未生成 {file_name}")

            # 創建處理結果摘要
            result_metadata = {
                "doc_id": doc_id,
                "original_file": file_path,
                "company_id": company_id,
                "file_size": Path(file_path).stat().st_size,
                "processing_method": "rag_anything_multimodal",
                "processing_time": processing_time,
                "created_at": datetime.now().isoformat(),
                "status": "completed",
                "generated_files": generated_files,
                "total_storage_size": total_size,
                "rag_config": {
                    "parser": self.rag_config.parser,
                    "parse_method": "auto",
                    "enable_image_processing": self.rag_config.enable_image_processing,
                    "enable_table_processing": self.rag_config.enable_table_processing,
                    "enable_equation_processing": self.rag_config.enable_equation_processing,
                },
            }

            # 保存元數據
            metadata_file = doc_folder / "processing_metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(result_metadata, f, ensure_ascii=False, indent=2)

            print(f"✅ 文檔處理完成: {doc_id}")
            print(
                f"   原始文件大小: {Path(file_path).stat().st_size / 1024 / 1024:.1f}MB"
            )
            print(f"   生成文件數量: {len(generated_files)}")
            print(f"   總存儲大小: {total_size / 1024 / 1024:.1f}MB")
            print(f"   處理時間: {processing_time:.2f}秒")
            print(f"   存儲位置: {doc_folder}")

            return {
                "status": "success",
                "doc_id": doc_id,
                "file_path": file_path,
                "processing_method": "rag_anything_multimodal",
                "generated_files": len(generated_files),
                "processing_time": processing_time,
                "storage_path": str(doc_folder),
                "total_size": total_size,
                "message": f"使用 RAG-Anything 成功處理文檔，生成 {len(generated_files)} 個存儲文件",
            }

        except Exception as e:
            print(f"❌ 文檔處理失敗: {e}")
            import traceback

            traceback.print_exc()

            return {
                "status": "error",
                "file_path": file_path,
                "error": str(e),
                "message": f"文檔處理失敗: {str(e)}",
            }

    async def delete_document(self, doc_id: str, company_id: str) -> Dict[str, Any]:
        """刪除文檔 - 使用獨立文件夾架構的原子刪除"""
        try:
            print(f"🗑️ 開始刪除文檔: {doc_id} (公司: {company_id})")

            # 構建文檔文件夾路徑
            company_dir = Path(f"./rag_storage/company_{company_id}")
            doc_folder = company_dir / doc_id

            if not doc_folder.exists():
                return {
                    "status": "error",
                    "message": f"文檔文件夾不存在: {doc_folder}",
                    "doc_id": doc_id,
                }

            # 計算文件夾大小（用於統計）
            folder_size = sum(
                f.stat().st_size for f in doc_folder.rglob("*") if f.is_file()
            )

            # 原子刪除整個文件夾
            import shutil

            shutil.rmtree(doc_folder)

            print(f"✅ 文檔刪除成功: {doc_id}")
            print(f"   釋放空間: {folder_size / 1024 / 1024:.1f}MB")

            return {
                "status": "success",
                "message": f"文檔 {doc_id} 已成功刪除",
                "doc_id": doc_id,
                "freed_space": folder_size,
                "freed_space_mb": folder_size / 1024 / 1024,
            }

        except Exception as e:
            print(f"❌ 文檔刪除失敗: {e}")
            return {
                "status": "error",
                "message": f"文檔刪除失敗: {str(e)}",
                "doc_id": doc_id,
            }

    async def query_documents(
        self, query: str, company_id: str, **kwargs
    ) -> Dict[str, Any]:
        """查詢文檔 - 基於獨立文件夾架構"""
        try:
            print(f"🔍 開始查詢: {query[:50]}... (公司: {company_id})")

            # 構建公司目錄路徑
            company_dir = Path(f"./rag_storage/company_{company_id}")

            if not company_dir.exists():
                return {
                    "status": "success",
                    "results": [],
                    "message": "公司目錄不存在",
                }

            # 收集所有文檔的結果
            all_results = []

            # 遍歷所有文檔文件夾
            for doc_folder in company_dir.iterdir():
                if doc_folder.is_dir():
                    try:
                        # 讀取文檔的元數據
                        metadata_file = doc_folder / "metadata.json"
                        if metadata_file.exists():
                            with open(metadata_file, "r", encoding="utf-8") as f:
                                metadata = json.load(f)

                            # 從實際的 LightRAG 文件中讀取內容
                            doc_content = ""
                            chunks_file = doc_folder / "kv_store_text_chunks.json"
                            if chunks_file.exists():
                                with open(chunks_file, "r", encoding="utf-8") as f:
                                    chunks_data = json.load(f)
                                    # LightRAG 的文本塊格式可能不同，需要適配
                                    if isinstance(chunks_data, dict):
                                        doc_content = " ".join(chunks_data.values())
                                    elif isinstance(chunks_data, list):
                                        doc_content = " ".join(
                                            [chunk["content"] if isinstance(chunk, dict) else str(chunk) for chunk in chunks_data]
                                        )

                            # 簡單的文本匹配
                            if query.lower() in doc_content.lower():
                                all_results.append(
                                    {
                                        "doc_id": doc_folder.name,  # 使用文件夾名作為 doc_id
                                        "score": 0.8,  # 模擬相關性分數
                                        "content": (
                                            doc_content[:200] + "..."
                                            if len(doc_content) > 200
                                            else doc_content
                                        ),
                                        "metadata": metadata if 'metadata' in locals() else {"doc_id": doc_folder.name},
                                    }
                                )

                    except Exception as e:
                        print(f"⚠️ 處理文檔文件夾失敗 {doc_folder.name}: {e}")

            # 按分數排序
            all_results.sort(key=lambda x: x["score"], reverse=True)

            print(f"✅ 查詢完成，找到 {len(all_results)} 個結果")

            return {
                "status": "success",
                "results": all_results,
                "total_results": len(all_results),
                "query": query,
            }

        except Exception as e:
            print(f"❌ 查詢失敗: {e}")
            return {
                "status": "error",
                "message": f"查詢失敗: {str(e)}",
                "query": query,
            }

    # 保留其他方法的佔位符實現
    async def process_document_with_cache(
        self, file_path: str, company_id: str
    ) -> Dict[str, Any]:
        """帶快取的文檔處理"""
        # 簡單實現，總是返回未命中
        return {"status": "miss", "message": "Cache miss, need to process"}

    async def process_folder(
        self, folder_path: str, company_id: str, output_dir: str = "./output"
    ) -> Dict[str, Any]:
        """批量處理文檔資料夾"""
        return {
            "status": "success",
            "processed_files": [],
            "total_files": 0,
            "message": "資料夾批量處理功能待實現",
        }

    async def insert_content_list(
        self, content_list: List[Dict], file_path: str, company_id: str
    ) -> Dict[str, Any]:
        """直接插入內容列表"""
        return {
            "status": "success",
            "message": "內容列表插入功能待實現",
        }


# 全域實例
_rag_service = None


def get_rag_service() -> RAGAnythingService:
    """取得 RAG 服務實例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGAnythingService()
    return _rag_service
