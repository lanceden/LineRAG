"""
RAG-Anything 服務整合
提供多模態文檔處理和查詢功能
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

from raganything import RAGAnything, RAGAnythingConfig
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

from dotenv import load_dotenv
load_dotenv()


class RAGAnythingService:
    """RAG-Anything 服務類"""

    def __init__(self):
        self.rag_instance = None
        self.initialized = False

    async def initialize(self):
        """初始化 RAG-Anything 系統"""
        if self.initialized:
            return

        try:
            # 取得環境變數
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")
            working_dir = os.getenv("RAG_WORKING_DIR", "./rag_storage")

            if not api_key:
                raise ValueError("OPENAI_API_KEY is required")

            # 創建工作目錄
            Path(working_dir).mkdir(parents=True, exist_ok=True)

            # 設定 RAG-Anything 配置
            config = RAGAnythingConfig(
                working_dir=working_dir,
                parser="mineru",  # 使用 MinerU 解析器
                parse_method="auto",  # 自動解析模式
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

            # 初始化 RAG-Anything
            self.rag_instance = RAGAnything(
                config=config,
                llm_model_func=llm_model_func,
                vision_model_func=vision_model_func,
                embedding_func=embedding_func,
            )

            self.initialized = True
            print("✅ RAG-Anything service initialized successfully")

        except Exception as e:
            print(f"❌ Failed to initialize RAG-Anything service: {e}")
            raise

    async def process_document(
        self, file_path: str, company_id: str, output_dir: str = "./output"
    ) -> Dict[str, Any]:
        """處理單個文檔"""
        if not self.initialized:
            await self.initialize()

        try:
            # 為每個公司創建獨立的輸出目錄
            company_output_dir = Path(output_dir) / company_id
            company_output_dir.mkdir(parents=True, exist_ok=True)

            # 處理文檔
            await self.rag_instance.process_document_complete(
                file_path=file_path,
                output_dir=str(company_output_dir),
                parse_method="auto",
            )

            return {
                "status": "success",
                "message": f"Document processed successfully for company {company_id}",
                "file_path": file_path,
                "output_dir": str(company_output_dir),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to process document: {str(e)}",
                "file_path": file_path,
            }

    async def process_folder(
        self, folder_path: str, company_id: str, output_dir: str = "./output"
    ) -> Dict[str, Any]:
        """批量處理文檔資料夾"""
        if not self.initialized:
            await self.initialize()

        try:
            # 為每個公司創建獨立的輸出目錄
            company_output_dir = Path(output_dir) / company_id
            company_output_dir.mkdir(parents=True, exist_ok=True)

            # 批量處理文檔
            await self.rag_instance.process_folder_complete(
                folder_path=folder_path,
                output_dir=str(company_output_dir),
                file_extensions=[".pdf", ".docx", ".pptx", ".xlsx", ".jpg", ".png"],
                recursive=True,
                max_workers=4,
            )

            return {
                "status": "success",
                "message": f"Folder processed successfully for company {company_id}",
                "folder_path": folder_path,
                "output_dir": str(company_output_dir),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to process folder: {str(e)}",
                "folder_path": folder_path,
            }

    async def query_text(self, query: str, mode: str = "hybrid") -> str:
        """純文本查詢"""
        if not self.initialized:
            await self.initialize()

        try:
            result = await self.rag_instance.aquery(query, mode=mode)
            return result
        except Exception as e:
            raise Exception(f"Query failed: {str(e)}")

    async def query_multimodal(
        self, query: str, multimodal_content: List[Dict], mode: str = "hybrid"
    ) -> str:
        """多模態查詢"""
        if not self.initialized:
            await self.initialize()

        try:
            result = await self.rag_instance.aquery_with_multimodal(
                query=query, multimodal_content=multimodal_content, mode=mode
            )
            return result
        except Exception as e:
            raise Exception(f"Multimodal query failed: {str(e)}")

    async def insert_content_list(
        self, content_list: List[Dict], file_path: str, company_id: str
    ) -> Dict[str, Any]:
        """直接插入內容列表"""
        if not self.initialized:
            await self.initialize()

        try:
            # 為公司添加標識
            doc_id = f"{company_id}_{Path(file_path).stem}"

            await self.rag_instance.insert_content_list(
                content_list=content_list,
                file_path=file_path,
                doc_id=doc_id,
                display_stats=True,
            )

            return {
                "status": "success",
                "message": f"Content list inserted successfully for company {company_id}",
                "doc_id": doc_id,
                "content_count": len(content_list),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to insert content list: {str(e)}",
                "file_path": file_path,
            }

    def get_status(self) -> Dict[str, Any]:
        """取得服務狀態"""
        return {
            "initialized": self.initialized,
            "rag_instance": self.rag_instance is not None,
            "service": "RAG-Anything",
        }


# 全域實例
_rag_service = None


def get_rag_service() -> RAGAnythingService:
    """取得 RAG-Anything 服務實例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGAnythingService()
    return _rag_service
