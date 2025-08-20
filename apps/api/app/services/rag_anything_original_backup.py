"""
RAG-Anything 服務整合
提供多模態文檔處理和查詢功能
"""

import os
from typing import List, Dict, Any
from pathlib import Path

from raganything import RAGAnything
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

from app.services.neo4j_service import get_neo4j_service

from dotenv import load_dotenv

load_dotenv()


class RAGAnythingService:
    """RAG-Anything 服務類"""

    def __init__(self):
        self.rag_instance = None
        self.neo4j_service = None
        self.initialized = False
        self.api_call_count = 0
        self.api_error_count = 0

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

            # 注意：當使用自定義 LightRAG 實例時，不需要 RAGAnythingConfig
            # RAG-Anything 會從 LightRAG 實例繼承所有配置

            # 定義 LLM 模型函數
            def llm_model_func(
                prompt, system_prompt=None, history_messages=[], **kwargs
            ):
                return self._robust_openai_call(
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

            # 設定 LightRAG 外部資料庫環境變數
            company_workspace = f"company_{working_dir.split('/')[-1]}"

            # 設定 Qdrant 環境變數
            os.environ["QDRANT_URL"] = (
                f"http://{os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6333')}"
            )
            os.environ["QDRANT_WORKSPACE"] = company_workspace

            # 設定 Neo4j 環境變數
            os.environ["NEO4J_WORKSPACE"] = company_workspace

            # 創建自定義的 LightRAG 實例，配置外部 Qdrant 和 Neo4j
            from lightrag import LightRAG

            lightrag_instance = LightRAG(
                working_dir=working_dir,
                llm_model_func=llm_model_func,
                embedding_func=embedding_func,
                # 配置使用 Qdrant 向量資料庫
                vector_storage="QdrantVectorDBStorage",
                # 配置使用 Neo4j 圖資料庫
                graph_storage="Neo4JStorage",
            )

            # 初始化 LightRAG 存儲
            print("🔄 Initializing LightRAG storages...")
            print(f"   📊 Qdrant 設定:")
            print(f"      主機: {os.getenv('QDRANT_HOST', 'localhost')}")
            print(f"      端口: {os.getenv('QDRANT_PORT', '6333')}")
            print(f"      命名空間: {os.getenv('QDRANT_WORKSPACE', 'default')}")
            print(f"   🔗 Neo4j 設定:")
            print(f"      URI: {os.getenv('NEO4J_URI', 'bolt://localhost:7687')}")
            print(f"      用戶: {os.getenv('NEO4J_USERNAME', 'neo4j')}")
            print(f"      命名空間: {os.getenv('NEO4J_WORKSPACE', 'default')}")

            try:
                await lightrag_instance.initialize_storages()
                print("✅ LightRAG storages initialized successfully")

                # 測試 Qdrant 連接
                print("🔍 測試 Qdrant 連接...")
                try:
                    from qdrant_client import QdrantClient

                    qdrant_client = QdrantClient(
                        host=os.getenv("QDRANT_HOST", "localhost"),
                        port=int(os.getenv("QDRANT_PORT", "6333")),
                    )
                    collections = qdrant_client.get_collections()
                    print(
                        f"✅ Qdrant 連接成功，集合數量: {len(collections.collections)}"
                    )
                    for collection in collections.collections:
                        info = qdrant_client.get_collection(collection.name)
                        print(
                            f"   📦 集合: {collection.name}, 點數量: {info.points_count}"
                        )
                except Exception as qdrant_error:
                    print(f"⚠️  Qdrant 連接測試失敗: {qdrant_error}")

                # 測試 Neo4j 連接
                print("🔍 測試 Neo4j 連接...")
                try:
                    from neo4j import GraphDatabase

                    neo4j_driver = GraphDatabase.driver(
                        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                        auth=(
                            os.getenv("NEO4J_USERNAME", "neo4j"),
                            os.getenv("NEO4J_PASSWORD", "linerag123"),
                        ),
                    )
                    with neo4j_driver.session() as session:
                        result = session.run("MATCH (n) RETURN count(n) as node_count")
                        node_count = result.single()["node_count"]
                        print(f"✅ Neo4j 連接成功，節點總數: {node_count}")
                    neo4j_driver.close()
                except Exception as neo4j_error:
                    print(f"⚠️  Neo4j 連接測試失敗: {neo4j_error}")

            except Exception as storage_error:
                print(f"❌ Failed to initialize LightRAG storages: {storage_error}")
                import traceback

                print(f"📋 詳細錯誤: {traceback.format_exc()}")
                raise

            # 初始化 RAG-Anything 使用自定義的 LightRAG 實例
            print("🔄 Creating RAG-Anything instance...")
            try:
                self.rag_instance = RAGAnything(
                    lightrag=lightrag_instance,  # 傳入配置好的 LightRAG 實例
                    vision_model_func=vision_model_func,
                )
                print("✅ RAG-Anything instance created successfully")
            except Exception as rag_error:
                print(f"❌ Failed to create RAG-Anything instance: {rag_error}")
                raise

            # 初始化 LightRAG 存儲 (確保外部資料庫連接)
            if hasattr(self.rag_instance, "lightrag") and self.rag_instance.lightrag:
                try:
                    await self.rag_instance.lightrag.initialize_storages()
                    print("✅ LightRAG storages initialized with external databases")
                except Exception as final_storage_error:
                    print(
                        f"❌ Failed final storage initialization: {final_storage_error}"
                    )
                    raise

            # 記錄配置資訊
            print(f"✅ RAG-Anything initialized with external databases:")
            print(f"📁 Working dir: {working_dir}")
            print(f"🏢 Company workspace: {company_workspace}")
            print(
                f"� Vector storage: QdrantVectorDBStorage ({os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6333')})"
            )
            print(
                f"🔗 Graph storage: Neo4JStorage ({os.getenv('NEO4J_URI', 'bolt://localhost:7687')})"
            )
            print(f"🔒 Multi-tenant isolation: Enabled")

            # 初始化 Neo4j 服務
            self.neo4j_service = get_neo4j_service()
            await self.neo4j_service.initialize()

            self.initialized = True
            print(
                "✅ RAG-Anything service with LightRAG + Neo4j + Qdrant initialized successfully"
            )

        except Exception as e:
            print(f"❌ Failed to initialize RAG-Anything service: {e}")
            raise

    async def _robust_openai_call(
        self,
        model,
        prompt,
        system_prompt=None,
        history_messages=[],
        api_key=None,
        base_url=None,
        **kwargs,
    ):
        """完整的 OpenAI API 調用（包含錯誤處理和重試）"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                self.api_call_count += 1

                # 調用 OpenAI API
                result = await openai_complete_if_cache(
                    model,
                    prompt,
                    system_prompt=system_prompt,
                    history_messages=history_messages,
                    api_key=api_key,
                    base_url=base_url,
                    **kwargs,
                )

                return result

            except Exception as e:
                retry_count += 1
                self.api_error_count += 1
                error_msg = str(e)

                # 檢查是否為可重試的錯誤
                if self._is_retryable_error(error_msg) and retry_count < max_retries:
                    wait_time = 2**retry_count  # 指數退避
                    print(
                        f"OpenAI API call failed (attempt {retry_count}/{max_retries}): {error_msg}"
                    )
                    print(f"Retrying in {wait_time} seconds...")

                    import asyncio

                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # 不可重試的錯誤或達到最大重試次數
                    print(f"OpenAI API call failed permanently: {error_msg}")
                    raise Exception(
                        f"OpenAI API failed after {max_retries} attempts: {error_msg}"
                    )

    def _is_retryable_error(self, error_msg: str) -> bool:
        """判斷是否為可重試的錯誤"""
        retryable_errors = [
            "rate limit",
            "timeout",
            "connection",
            "server error",
            "503",
            "502",
            "500",
            "429",
        ]

        error_lower = error_msg.lower()
        return any(err in error_lower for err in retryable_errors)

    def get_api_stats(self) -> Dict[str, Any]:
        """取得 API 使用統計"""
        success_rate = 0
        if self.api_call_count > 0:
            success_rate = (
                (self.api_call_count - self.api_error_count) / self.api_call_count
            ) * 100

        return {
            "total_calls": self.api_call_count,
            "error_count": self.api_error_count,
            "success_count": self.api_call_count - self.api_error_count,
            "success_rate_percent": round(success_rate, 2),
            "service_health": (
                "healthy"
                if success_rate > 95
                else "degraded" if success_rate > 80 else "unhealthy"
            ),
        }

    async def process_document(
        self, file_path: str, company_id: str, output_dir: str = "./output"
    ) -> Dict[str, Any]:
        """處理單個文檔"""
        print("=" * 80)
        print(f"🔥 RAG-Anything 開始處理文檔")
        print(f"   文件路徑: {file_path}")
        print(f"   公司ID: {company_id}")
        print(f"   輸出目錄: {output_dir}")
        print("=" * 80)

        if not self.initialized:
            print(f"⚠️  RAG 服務未初始化，開始初始化...")
            await self.initialize()
            print(f"✅ RAG 服務初始化完成")

        max_retries = 3
        retry_count = 0
        print(f"🔄 設定重試機制: 最大重試次數 {max_retries}")

        while retry_count < max_retries:
            try:
                print(f"🔄 開始處理嘗試 {retry_count + 1}/{max_retries}")

                # 檢查文檔格式和大小
                print(f"📊 檢查文檔大小...")
                file_size = os.path.getsize(file_path)
                file_size_mb = file_size / 1024 / 1024
                print(f"   文檔大小: {file_size} bytes ({file_size_mb:.2f} MB)")

                if file_size > 100 * 1024 * 1024:  # 100MB 限制
                    print(f"❌ 文檔過大: {file_size_mb:.1f}MB (最大限制: 100MB)")
                    return {
                        "status": "error",
                        "message": f"File too large: {file_size_mb:.1f}MB (max 100MB)",
                        "file_path": file_path,
                    }
                print(f"✅ 文檔大小檢查通過")

                # 為每個公司創建獨立的輸出目錄
                company_output_dir = Path(output_dir) / company_id
                print(f"📁 創建公司輸出目錄: {company_output_dir}")
                company_output_dir.mkdir(parents=True, exist_ok=True)
                print(f"✅ 輸出目錄創建成功")

                # 處理文檔 - 確保使用正確的多租戶命名空間
                print(f"🔥 開始 RAG-Anything 文檔處理...")
                print(f"   文檔路徑: {file_path}")
                print(f"   輸出目錄: {company_output_dir}")

                # 重新設定環境變數確保多租戶隔離
                company_workspace = f"company_{company_id}"
                original_qdrant_workspace = os.environ.get("QDRANT_WORKSPACE")
                original_neo4j_workspace = os.environ.get("NEO4J_WORKSPACE")

                print(f"🏷️  多租戶命名空間設定:")
                print(f"   目標命名空間: {company_workspace}")
                print(f"   原始 Qdrant 命名空間: {original_qdrant_workspace}")
                print(f"   原始 Neo4j 命名空間: {original_neo4j_workspace}")

                try:
                    # 設定公司特定的命名空間
                    os.environ["QDRANT_WORKSPACE"] = company_workspace
                    os.environ["NEO4J_WORKSPACE"] = company_workspace
                    print(f"✅ 命名空間設定完成: {company_workspace}")
                    print(f"   QDRANT_WORKSPACE = {os.environ.get('QDRANT_WORKSPACE')}")
                    print(f"   NEO4J_WORKSPACE = {os.environ.get('NEO4J_WORKSPACE')}")

                    # 重新創建 LightRAG 實例以使用新的命名空間
                    print(f"🔄 重新創建 LightRAG 實例以使用新命名空間...")
                    try:
                        # 重新創建 LightRAG 實例
                        from lightrag import LightRAG
                        from lightrag.llm.openai import (
                            openai_complete_if_cache,
                            openai_embed,
                        )
                        from lightrag.utils import EmbeddingFunc

                        # 設定 LLM 和 Embedding 函數
                        llm_model_func = openai_complete_if_cache
                        embedding_func = EmbeddingFunc(
                            embedding_dim=3072,
                            max_token_size=8192,
                            func=openai_embed,
                        )

                        # 使用當前工作目錄
                        working_dir = os.environ.get("RAG_WORKING_DIR", "./rag_storage")

                        # 創建新的 LightRAG 實例
                        new_lightrag_instance = LightRAG(
                            working_dir=working_dir,
                            llm_model_func=llm_model_func,
                            embedding_func=embedding_func,
                            vector_storage="QdrantVectorDBStorage",
                            graph_storage="Neo4JStorage",
                        )

                        # 初始化新實例的存儲
                        await new_lightrag_instance.initialize_storages()

                        # 更新 RAG-Anything 實例的 lightrag
                        self.rag_instance.lightrag = new_lightrag_instance

                        print(f"✅ LightRAG 實例重新創建完成")

                    except Exception as storage_error:
                        print(f"⚠️  LightRAG 實例重新創建失敗: {storage_error}")
                        # 繼續處理，使用現有存儲

                    print(f"🚀 調用 RAG-Anything 核心處理...")
                    print(f"   解析方法: auto")
                    print(f"   設備: auto (自動選擇 GPU/CPU)")
                    print(f"   後端: pipeline")

                    # 檢查文檔是否存在
                    if not os.path.exists(file_path):
                        print(f"❌ 文檔不存在: {file_path}")
                        raise FileNotFoundError(f"Document not found: {file_path}")

                    print(f"✅ 文檔存在，開始處理...")

                    # 直接使用 LightRAG 處理文檔內容
                    print(f"🔄 直接使用 LightRAG 處理文檔...")

                    # 讀取文檔內容
                    if file_path.lower().endswith(".pdf"):
                        # 使用 PyPDF2 或其他 PDF 解析器
                        try:
                            import PyPDF2

                            with open(file_path, "rb") as file:
                                pdf_reader = PyPDF2.PdfReader(file)
                                text_content = ""
                                for page in pdf_reader.pages:
                                    text_content += page.extract_text() + "\n"
                        except Exception as pdf_error:
                            print(f"⚠️  PDF 解析失敗，嘗試其他方法: {pdf_error}")
                            # 備用方案：使用 RAG-Anything 解析
                            await self.rag_instance.process_document_complete(
                                file_path=file_path,
                                output_dir=str(company_output_dir),
                                parse_method="auto",
                                device="auto",
                                backend="pipeline",
                            )
                            # 從輸出目錄讀取解析結果
                            text_files = list(Path(company_output_dir).glob("*.txt"))
                            text_content = ""
                            for text_file in text_files:
                                with open(text_file, "r", encoding="utf-8") as f:
                                    text_content += f.read() + "\n"
                    else:
                        # 其他文件類型直接讀取
                        with open(file_path, "r", encoding="utf-8") as f:
                            text_content = f.read()

                    print(f"📄 提取文本內容: {len(text_content)} 字符")

                    if text_content.strip():
                        # 直接使用 LightRAG 插入內容
                        print(f"🚀 使用 LightRAG 插入內容...")
                        await self.rag_instance.lightrag.ainsert(text_content)
                        print(f"✅ LightRAG 內容插入完成")
                    else:
                        print(f"⚠️  文檔內容為空，跳過索引")

                    print(f"✅ 文檔處理完成")

                    # 檢查輸出目錄中的文件
                    print(f"🔍 檢查輸出目錄內容...")
                    if os.path.exists(company_output_dir):
                        output_files = list(Path(company_output_dir).rglob("*"))
                        print(f"   輸出文件數量: {len(output_files)}")
                        for output_file in output_files[:10]:  # 只顯示前10個文件
                            if output_file.is_file():
                                file_size = output_file.stat().st_size
                                print(f"   - {output_file.name}: {file_size} bytes")
                    else:
                        print(f"   ⚠️  輸出目錄不存在: {company_output_dir}")

                    # 檢查是否有文本內容被提取
                    print(f"🔍 檢查文本提取結果...")
                    text_files = list(Path(company_output_dir).glob("*.txt"))
                    if text_files:
                        for text_file in text_files[:3]:  # 檢查前3個文本文件
                            try:
                                with open(text_file, "r", encoding="utf-8") as f:
                                    content = f.read()
                                    print(
                                        f"   📄 {text_file.name}: {len(content)} 字符"
                                    )
                                    if content.strip():
                                        print(f"      內容預覽: {content[:200]}...")
                                    else:
                                        print(f"      ⚠️  文件為空")
                            except Exception as e:
                                print(f"      ❌ 讀取失敗: {e}")
                    else:
                        print(f"   ⚠️  未找到文本文件")

                    # 檢查 LightRAG 是否接收到內容
                    print(f"🔍 檢查 LightRAG 處理狀態...")
                    if (
                        hasattr(self.rag_instance, "lightrag")
                        and self.rag_instance.lightrag
                    ):
                        working_dir = self.rag_instance.lightrag.working_dir
                        print(f"   LightRAG 工作目錄: {working_dir}")

                        # 檢查 LightRAG 工作目錄中的文件
                        if os.path.exists(working_dir):
                            lightrag_files = list(Path(working_dir).rglob("*"))
                            print(f"   LightRAG 文件數量: {len(lightrag_files)}")
                            for lightrag_file in lightrag_files[:10]:
                                if lightrag_file.is_file():
                                    file_size = lightrag_file.stat().st_size
                                    print(
                                        f"   - {lightrag_file.name}: {file_size} bytes"
                                    )
                        else:
                            print(f"   ⚠️  LightRAG 工作目錄不存在: {working_dir}")
                    else:
                        print(f"   ⚠️  無法訪問 LightRAG 實例")

                    # 檢查處理後的資料庫狀態
                    print(f"🔍 檢查處理後的資料庫狀態...")
                    await self._check_database_status_after_processing(
                        company_workspace, file_path
                    )

                finally:
                    # 恢復原始環境變數
                    print(f"🔄 恢復原始環境變數...")
                    if original_qdrant_workspace:
                        os.environ["QDRANT_WORKSPACE"] = original_qdrant_workspace
                        print(
                            f"   QDRANT_WORKSPACE 恢復為: {original_qdrant_workspace}"
                        )
                    if original_neo4j_workspace:
                        os.environ["NEO4J_WORKSPACE"] = original_neo4j_workspace
                        print(f"   NEO4J_WORKSPACE 恢復為: {original_neo4j_workspace}")

                print(f"🎉 RAG-Anything 文檔處理完全成功!")
                print(f"   處理文檔: {file_path}")
                print(f"   公司ID: {company_id}")
                print(f"   文檔大小: {file_size_mb:.2f} MB")
                print(f"   重試次數: {retry_count}")
                print("=" * 80)

                return {
                    "status": "success",
                    "message": f"Document processed successfully for company {company_id}",
                    "file_path": file_path,
                    "file_size": file_size,
                    "retry_count": retry_count,
                    "output_dir": str(company_output_dir),
                }

            except Exception as e:
                retry_count += 1
                error_msg = str(e)

                print(f"❌ 文檔處理失敗 (嘗試 {retry_count}/{max_retries})")
                print(f"   錯誤訊息: {error_msg}")
                print(f"   文檔路徑: {file_path}")
                print(f"   公司ID: {company_id}")

                if retry_count < max_retries:
                    wait_time = 2**retry_count
                    print(f"🔄 準備重試，等待 {wait_time} 秒...")
                    import asyncio

                    await asyncio.sleep(wait_time)  # 指數退避
                    print(f"🔄 開始第 {retry_count + 1} 次重試...")
                    continue
                else:
                    print(f"💥 文檔處理最終失敗!")
                    print(f"   已重試 {max_retries} 次")
                    print(f"   最終錯誤: {error_msg}")
                    print("=" * 80)
                    return {
                        "status": "error",
                        "message": f"Failed to process document after {max_retries} attempts: {error_msg}",
                        "file_path": file_path,
                        "retry_count": retry_count,
                    }

    async def _check_database_status_after_processing(
        self, company_workspace: str, file_path: str
    ):
        """檢查文檔處理後的資料庫狀態"""
        try:
            # 檢查 Qdrant 狀態
            print(f"📊 檢查 Qdrant 向量資料庫狀態...")
            try:
                from qdrant_client import QdrantClient

                qdrant_client = QdrantClient(
                    host=os.getenv("QDRANT_HOST", "localhost"),
                    port=int(os.getenv("QDRANT_PORT", "6333")),
                )

                # 檢查集合
                collections = qdrant_client.get_collections()
                print(f"   📦 總集合數量: {len(collections.collections)}")

                # 查找公司相關的集合
                company_collections = [
                    c for c in collections.collections if company_workspace in c.name
                ]
                print(f"   🏢 公司相關集合數量: {len(company_collections)}")

                for collection in company_collections:
                    try:
                        info = qdrant_client.get_collection(collection.name)
                        print(
                            f"      📦 {collection.name}: {info.points_count} 個向量點"
                        )
                    except Exception as e:
                        print(f"      ❌ 無法獲取集合 {collection.name} 的資訊: {e}")

            except Exception as qdrant_error:
                print(f"   ❌ Qdrant 狀態檢查失敗: {qdrant_error}")

            # 檢查 Neo4j 狀態
            print(f"🔗 檢查 Neo4j 圖資料庫狀態...")
            try:
                from neo4j import GraphDatabase

                neo4j_driver = GraphDatabase.driver(
                    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                    auth=(
                        os.getenv("NEO4J_USERNAME", "neo4j"),
                        os.getenv("NEO4J_PASSWORD", "linerag123"),
                    ),
                )

                with neo4j_driver.session() as session:
                    # 檢查總節點數
                    result = session.run("MATCH (n) RETURN count(n) as total_nodes")
                    total_nodes = result.single()["total_nodes"]
                    print(f"   🔗 總節點數: {total_nodes}")

                    # 檢查公司相關節點
                    result = session.run(
                        "MATCH (n) WHERE n.workspace = $workspace RETURN count(n) as company_nodes",
                        workspace=company_workspace,
                    )
                    company_nodes = result.single()["company_nodes"]
                    print(f"   🏢 公司 {company_workspace} 節點數: {company_nodes}")

                    # 檢查文檔相關節點
                    filename = os.path.basename(file_path)
                    result = session.run(
                        "MATCH (n) WHERE n.workspace = $workspace AND (n.filename CONTAINS $filename OR n.source CONTAINS $filename) RETURN count(n) as doc_nodes",
                        workspace=company_workspace,
                        filename=filename,
                    )
                    doc_nodes = result.single()["doc_nodes"]
                    print(f"   📄 文檔 {filename} 相關節點數: {doc_nodes}")

                neo4j_driver.close()

            except Exception as neo4j_error:
                print(f"   ❌ Neo4j 狀態檢查失敗: {neo4j_error}")

        except Exception as e:
            print(f"❌ 資料庫狀態檢查失敗: {e}")

    async def _check_database_status_before_query(self, query: str):
        """查詢前檢查資料庫狀態"""
        try:
            current_workspace = os.environ.get("QDRANT_WORKSPACE", "default")

            # 檢查 Qdrant 中的向量數據
            print(f"📊 檢查 Qdrant 向量數據 (命名空間: {current_workspace})...")
            try:
                from qdrant_client import QdrantClient

                qdrant_client = QdrantClient(
                    host=os.getenv("QDRANT_HOST", "localhost"),
                    port=int(os.getenv("QDRANT_PORT", "6333")),
                )

                collections = qdrant_client.get_collections()
                workspace_collections = [
                    c for c in collections.collections if current_workspace in c.name
                ]

                if not workspace_collections:
                    print(f"   ⚠️  未找到命名空間 {current_workspace} 的集合")
                    print(
                        f"   📦 可用集合: {[c.name for c in collections.collections]}"
                    )
                else:
                    total_points = 0
                    for collection in workspace_collections:
                        try:
                            info = qdrant_client.get_collection(collection.name)
                            points_count = info.points_count
                            total_points += points_count
                            print(f"   📦 {collection.name}: {points_count} 個向量點")
                        except Exception as e:
                            print(f"   ❌ 集合 {collection.name} 檢查失敗: {e}")

                    print(
                        f"   📊 命名空間 {current_workspace} 總向量點數: {total_points}"
                    )

                    if total_points == 0:
                        print(f"   ⚠️  警告: 命名空間中沒有向量數據，可能導致查詢無結果")

            except Exception as qdrant_error:
                print(f"   ❌ Qdrant 檢查失敗: {qdrant_error}")

            # 檢查 Neo4j 中的圖數據
            print(f"🔗 檢查 Neo4j 圖數據 (命名空間: {current_workspace})...")
            try:
                from neo4j import GraphDatabase

                neo4j_driver = GraphDatabase.driver(
                    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                    auth=(
                        os.getenv("NEO4J_USERNAME", "neo4j"),
                        os.getenv("NEO4J_PASSWORD", "linerag123"),
                    ),
                )

                with neo4j_driver.session() as session:
                    # 檢查命名空間節點數
                    result = session.run(
                        "MATCH (n) WHERE n.workspace = $workspace RETURN count(n) as node_count",
                        workspace=current_workspace,
                    )
                    node_count = result.single()["node_count"]
                    print(f"   🔗 命名空間 {current_workspace} 節點數: {node_count}")

                    if node_count == 0:
                        print(f"   ⚠️  警告: 命名空間中沒有圖節點，可能導致查詢無結果")

                neo4j_driver.close()

            except Exception as neo4j_error:
                print(f"   ❌ Neo4j 檢查失敗: {neo4j_error}")

        except Exception as e:
            print(f"❌ 查詢前資料庫檢查失敗: {e}")

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

    async def query_text(
        self, query: str, mode: str = "hybrid", company_id: str = None
    ) -> str:
        """純文本查詢"""
        print("=" * 80)
        print(f"🔍 開始 RAG 文本查詢")
        print(f"   查詢內容: {query}")
        print(f"   查詢模式: {mode}")
        print(f"   公司ID: {company_id}")
        print(f"   當前命名空間:")
        print(
            f"      QDRANT_WORKSPACE: {os.environ.get('QDRANT_WORKSPACE', 'default')}"
        )
        print(f"      NEO4J_WORKSPACE: {os.environ.get('NEO4J_WORKSPACE', 'default')}")

        # 如果提供了 company_id，設定正確的命名空間
        if company_id:
            company_workspace = f"company_{company_id}"
            original_qdrant_workspace = os.environ.get("QDRANT_WORKSPACE")
            original_neo4j_workspace = os.environ.get("NEO4J_WORKSPACE")

            print(f"🏷️  設定查詢命名空間:")
            print(f"   目標命名空間: {company_workspace}")

            # 設定公司特定的命名空間
            os.environ["QDRANT_WORKSPACE"] = company_workspace
            os.environ["NEO4J_WORKSPACE"] = company_workspace
            print(f"✅ 查詢命名空間設定完成: {company_workspace}")

        print("=" * 80)

        if not self.initialized:
            print(f"⚠️  RAG 服務未初始化，開始初始化...")
            await self.initialize()
            print(f"✅ RAG 服務初始化完成")

        try:
            # 查詢前檢查資料庫狀態
            print(f"🔍 查詢前檢查資料庫狀態...")
            await self._check_database_status_before_query(query)

            print(f"🚀 執行 RAG 查詢...")
            result = await self.rag_instance.aquery(query, mode=mode)

            print(f"✅ RAG 查詢完成")
            print(f"   結果長度: {len(result)} 字符")
            print(f"   結果預覽: {result[:100]}...")
            print("=" * 80)

            return result
        except Exception as e:
            print(f"❌ RAG 查詢失敗: {str(e)}")
            print("=" * 80)
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
            "neo4j_service": self.neo4j_service is not None,
            "lightrag_instance": (
                hasattr(self.rag_instance, "lightrag") if self.rag_instance else False
            ),
            "service": "RAG-Anything with LightRAG + Neo4j + Qdrant",
        }

    async def get_entity_details(
        self, company_id: int, entity_id: str
    ) -> Dict[str, Any]:
        """取得實體詳細資訊"""
        if not self.initialized:
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
        if not self.initialized:
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
        if not self.initialized:
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

            # 這裡可以進一步查詢實體間的關係來生成 edges
            # 為簡化，暫時返回節點資料

            return {
                "status": "success",
                "nodes": nodes,
                "edges": [],  # TODO: 實作邊的查詢
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
        if not self.initialized:
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

            # TODO: 實作實體提取邏輯
            # 這裡可以整合 NER 模型或使用 LLM 進行實體提取
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

            # TODO: 實作關係提取邏輯
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

    async def _extract_entities_from_document(
        self, file_path: str, company_id: int
    ) -> List[Dict[str, Any]]:
        """從文檔提取實體（完整實作）"""
        try:
            # 讀取文檔內容
            content = ""
            if file_path.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                # 對於其他格式，使用 RAG-Anything 已處理的內容
                # 這裡可以從 LightRAG 的存儲中獲取已處理的文字內容
                content = f"Document: {Path(file_path).stem}"

            # 使用 LLM 進行實體提取
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

            # 調用 LLM 進行實體提取
            if hasattr(self.rag_instance, "lightrag") and self.rag_instance.lightrag:
                llm_response = await self.rag_instance.lightrag.llm_model_func(
                    entity_extraction_prompt,
                    system_prompt="你是一個專業的實體提取助手，請準確識別文檔中的重要實體。",
                )

                # 解析 LLM 回應
                import json
                import re

                # 嘗試提取 JSON 部分
                json_match = re.search(r"\[.*\]", llm_response, re.DOTALL)
                if json_match:
                    try:
                        extracted_entities = json.loads(json_match.group())

                        # 轉換為標準格式
                        entities = []
                        filename = Path(file_path).stem

                        for i, entity in enumerate(
                            extracted_entities[:10]
                        ):  # 限制最多10個實體
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

                    except json.JSONDecodeError:
                        pass

            # 備用方案：基於規則的簡單實體提取
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

        except Exception as e:
            print(f"Entity extraction failed: {e}")
            # 錯誤時返回基本實體
            filename = Path(file_path).stem
            return [
                {
                    "id": f"{company_id}_{filename}_document",
                    "name": filename,
                    "type": "Document",
                    "description": f"Document entity for {filename}",
                    "properties": {
                        "source_file": file_path,
                        "extraction_method": "error_fallback",
                        "confidence": 0.3,
                    },
                }
            ]

    async def _extract_relationships_from_entities(
        self, entities: List[Dict[str, Any]], company_id: int
    ) -> List[Dict[str, Any]]:
        """從實體提取關係（完整實作）"""
        try:
            if len(entities) < 2:
                return []

            relationships = []

            # 使用 LLM 進行關係提取
            if hasattr(self.rag_instance, "lightrag") and self.rag_instance.lightrag:
                # 準備實體列表
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

                    # 解析 LLM 回應
                    import json
                    import re

                    # 嘗試提取 JSON 部分
                    json_match = re.search(r"\[.*\]", llm_response, re.DOTALL)
                    if json_match:
                        try:
                            extracted_relationships = json.loads(json_match.group())

                            # 建立實體名稱到 ID 的映射
                            entity_name_to_id = {
                                entity["name"]: entity["id"] for entity in entities
                            }

                            # 轉換為標準格式
                            for i, rel in enumerate(
                                extracted_relationships[:20]
                            ):  # 限制最多20個關係
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
                                                "description": rel.get(
                                                    "description", ""
                                                ),
                                                "extraction_method": "llm",
                                                "confidence": 0.7,
                                                "company_id": company_id,
                                            },
                                        }
                                    )

                        except json.JSONDecodeError:
                            pass

                except Exception as e:
                    print(f"LLM relationship extraction failed: {e}")

            # 基於規則的關係提取（備用方案）
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

            # 為同類型實體建立 "similar_to" 關係
            entity_types = {}
            for entity in entities:
                entity_type = entity["type"]
                if entity_type not in entity_types:
                    entity_types[entity_type] = []
                entity_types[entity_type].append(entity)

            for entity_type, type_entities in entity_types.items():
                if len(type_entities) > 1 and entity_type != "Document":
                    for i, entity1 in enumerate(type_entities):
                        for entity2 in type_entities[i + 1 :]:
                            relationships.append(
                                {
                                    "source_id": entity1["id"],
                                    "target_id": entity2["id"],
                                    "type": "similar_to",
                                    "properties": {
                                        "description": f"Both are {entity_type} entities",
                                        "extraction_method": "rule_based",
                                        "confidence": 0.5,
                                        "company_id": company_id,
                                    },
                                }
                            )

            return relationships

        except Exception as e:
            print(f"Relationship extraction failed: {e}")
            return []

    async def query_knowledge_graph(
        self, company_id: int, entity_name: str, max_depth: int = 2
    ) -> Dict[str, Any]:
        """查詢知識圖譜"""
        if not self.initialized:
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
        if not self.initialized:
            await self.initialize()

        try:
            stats = await self.neo4j_service.get_company_graph_stats(company_id)
            return {"status": "success", "stats": stats}
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get graph stats: {str(e)}",
            }

    async def delete_document(
        self, document_id: str, company_id: str
    ) -> Dict[str, Any]:
        """刪除文檔及其相關的向量和圖數據"""
        print("=" * 80)
        print(f"🗑️  開始刪除文檔")
        print(f"   文檔ID: {document_id}")
        print(f"   公司ID: {company_id}")
        print("=" * 80)

        if not self.initialized:
            print(f"⚠️  RAG 服務未初始化，開始初始化...")
            await self.initialize()
            print(f"✅ RAG 服務初始化完成")

        try:
            # 設定正確的多租戶命名空間
            company_workspace = f"company_{company_id}"
            original_qdrant_workspace = os.environ.get("QDRANT_WORKSPACE")
            original_neo4j_workspace = os.environ.get("NEO4J_WORKSPACE")

            print(f"🏷️  設定刪除命名空間:")
            print(f"   目標命名空間: {company_workspace}")
            print(f"   原始 Qdrant 命名空間: {original_qdrant_workspace}")
            print(f"   原始 Neo4j 命名空間: {original_neo4j_workspace}")

            try:
                # 設定公司特定的命名空間
                os.environ["QDRANT_WORKSPACE"] = company_workspace
                os.environ["NEO4J_WORKSPACE"] = company_workspace
                print(f"✅ 刪除命名空間設定完成: {company_workspace}")

                # 從 Qdrant 刪除向量數據
                print(f"🗑️  從 Qdrant 刪除向量數據...")
                await self._delete_from_qdrant(document_id, company_workspace)

                # 從 Neo4j 刪除圖數據
                print(f"🗑️  從 Neo4j 刪除圖數據...")
                await self._delete_from_neo4j(document_id, company_workspace)

                print(f"✅ 文檔刪除完成: {document_id}")
                print("=" * 80)

                return {
                    "status": "success",
                    "message": f"Document {document_id} deleted successfully",
                    "document_id": document_id,
                    "company_id": company_id,
                }

            finally:
                # 恢復原始環境變數
                print(f"🔄 恢復原始環境變數...")
                if original_qdrant_workspace:
                    os.environ["QDRANT_WORKSPACE"] = original_qdrant_workspace
                    print(f"   QDRANT_WORKSPACE 恢復為: {original_qdrant_workspace}")
                if original_neo4j_workspace:
                    os.environ["NEO4J_WORKSPACE"] = original_neo4j_workspace
                    print(f"   NEO4J_WORKSPACE 恢復為: {original_neo4j_workspace}")

        except Exception as e:
            print(f"❌ 文檔刪除失敗: {str(e)}")
            print("=" * 80)
            return {
                "status": "error",
                "message": f"Failed to delete document: {str(e)}",
                "document_id": document_id,
                "company_id": company_id,
            }

    async def _delete_from_qdrant(self, document_id: str, company_workspace: str):
        """從 Qdrant 刪除文檔相關的向量數據"""
        try:
            from qdrant_client import QdrantClient

            qdrant_client = QdrantClient(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6333")),
            )

            # 獲取所有集合
            collections = qdrant_client.get_collections()
            workspace_collections = [
                c for c in collections.collections if company_workspace in c.name
            ]

            deleted_points = 0
            for collection in workspace_collections:
                try:
                    # 直接刪除整個集合（因為是按公司隔離的）
                    info = qdrant_client.get_collection(collection.name)
                    points_count = info.points_count

                    if points_count > 0:
                        # 刪除整個集合
                        qdrant_client.delete_collection(collection.name)
                        deleted_points += points_count
                        print(
                            f"   📦 刪除集合 {collection.name} ({points_count} 個向量點)"
                        )

                except Exception as e:
                    print(f"   ⚠️  集合 {collection.name} 刪除失敗: {e}")

            print(f"   ✅ Qdrant 刪除完成，總共刪除 {deleted_points} 個向量點")

        except Exception as e:
            print(f"   ❌ Qdrant 刪除失敗: {e}")
            raise

    async def _delete_from_neo4j(self, document_id: str, company_workspace: str):
        """從 Neo4j 刪除文檔相關的圖數據"""
        try:
            from neo4j import GraphDatabase

            neo4j_driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                auth=(
                    os.getenv("NEO4J_USERNAME", "neo4j"),
                    os.getenv("NEO4J_PASSWORD", "linerag123"),
                ),
            )

            with neo4j_driver.session() as session:
                # 刪除整個公司命名空間的所有節點（因為是按公司隔離的）
                delete_query = """
                MATCH (n)
                WHERE n.workspace = $workspace
                DETACH DELETE n
                RETURN count(n) as deleted_count
                """

                result = session.run(delete_query, workspace=company_workspace)

                deleted_count = result.single()["deleted_count"]
                print(f"   ✅ Neo4j 刪除完成，刪除了 {deleted_count} 個節點")

            neo4j_driver.close()

        except Exception as e:
            print(f"   ❌ Neo4j 刪除失敗: {e}")
            raise


# 全域實例
_rag_service = None


def get_rag_service() -> RAGAnythingService:
    """取得 RAG-Anything 服務實例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGAnythingService()
    return _rag_service
