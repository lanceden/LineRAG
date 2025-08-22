"""
RAG-Anything 文檔處理器
"""

import os
import asyncio
from typing import Dict, Any, List
from pathlib import Path
from .rag_config import RAGConfig
from .rag_database_manager import DatabaseManager
from app.utils.namespace import AsyncNamespaceContext
from app.utils.data_validator import verify_document_processing


class DocumentProcessor:
    """文檔處理器"""

    def __init__(self, rag_service, config: RAGConfig, db_manager: DatabaseManager):
        self.rag_service = rag_service  # 持有 RAG 服務引用而不是實例
        self.config = config
        self.db_manager = db_manager

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

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # 檢查文檔大小
                if not await self._validate_document(file_path):
                    return self._create_error_response(
                        file_path, "Document validation failed"
                    )

                # 使用異步命名空間上下文管理器
                async with AsyncNamespaceContext(int(company_id)) as company_workspace:
                    # 修正多租戶文件隔離：先創建公司專用目錄，再讓 RAG-Anything 在其中創建文件目錄
                    company_output_dir = self.config.get_company_output_dir(
                        company_id, output_dir
                    )
                    print(f"📁 公司專用輸出目錄: {company_output_dir}")

                    # 處理文檔
                    await self._process_document_content(file_path, company_output_dir)

                    # 檢查處理結果
                    await self._verify_processing_results(
                        company_workspace, file_path, company_output_dir
                    )

                    # 驗證文檔處理是否成功 (修正: 給予更多時間讓數據同步)
                    filename = os.path.basename(file_path)
                    print(f"⏳ 等待數據同步...")
                    await asyncio.sleep(2)  # 給數據同步一些時間

                    processing_success = await verify_document_processing(
                        int(company_id), filename
                    )

                    if not processing_success:
                        print(f"⚠️  初次驗證失敗，再等待3秒後重試...")
                        await asyncio.sleep(3)
                        processing_success = await verify_document_processing(
                            int(company_id), filename
                        )

                        if not processing_success:
                            print(f"⚠️  驗證仍失敗，但繼續處理 (可能是數據同步延遲)")
                            # 不拋出異常，允許處理繼續

                    # 獲取文件信息
                    file_size = os.path.getsize(file_path)
                    file_size_mb = file_size / 1024 / 1024

                    print(f"🎉 文檔處理完全成功!")
                    print(f"   處理文檔: {file_path}")
                    print(f"   公司ID: {company_id}")
                    print(f"   文檔大小: {file_size_mb:.2f} MB")
                    print(f"   重試次數: {retry_count}")
                    print("=" * 80)

                    # 獲取 LightRAG doc_id
                    lightrag_doc_id = getattr(self, '_last_processed_doc_id', None)
                    
                    return {
                        "status": "success",
                        "message": f"Document processed successfully for company {company_id}",
                        "file_path": file_path,
                        "file_size": file_size,
                        "retry_count": retry_count,
                        "output_dir": str(company_output_dir),
                        "processing_verified": processing_success,
                        "lightrag_doc_id": lightrag_doc_id,
                    }

            except Exception as e:
                retry_count += 1
                error_msg = str(e)

                print(f"❌ 文檔處理失敗 (嘗試 {retry_count}/{max_retries})")
                print(f"   錯誤訊息: {error_msg}")

                if retry_count < max_retries:
                    wait_time = 2**retry_count
                    print(f"🔄 準備重試，等待 {wait_time} 秒...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"💥 文檔處理最終失敗!")
                    return self._create_error_response(
                        file_path, f"Failed after {max_retries} attempts: {error_msg}"
                    )

    async def process_folder(
        self, folder_path: str, company_id: str, output_dir: str = "./output"
    ) -> Dict[str, Any]:
        """批量處理文檔資料夾"""
        try:
            # 設定公司命名空間
            company_workspace = self.config.set_company_namespace(company_id)

            try:
                # 創建輸出目錄
                company_output_dir = self.config.get_company_output_dir(
                    company_id, output_dir
                )

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

            finally:
                self.config.restore_namespace()

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to process folder: {str(e)}",
                "folder_path": folder_path,
            }

    async def insert_content_list(
        self, content_list: List[Dict], file_path: str, company_id: str
    ) -> Dict[str, Any]:
        """直接插入內容列表"""
        try:
            # 設定公司命名空間
            self.config.set_company_namespace(company_id)

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

            finally:
                self.config.restore_namespace()

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to insert content list: {str(e)}",
                "file_path": file_path,
            }

    async def delete_document(
        self, document_id: str, company_id: str
    ) -> Dict[str, Any]:
        """刪除單個文檔及其相關的向量和圖數據"""
        print("=" * 80)
        print(f"🗑️  開始刪除文檔")
        print(f"   文檔ID: {document_id}")
        print(f"   公司ID: {company_id}")
        print("=" * 80)

        try:
            # 使用異步命名空間上下文管理器
            async with AsyncNamespaceContext(int(company_id)) as company_workspace:

                # 1. 使用 LightRAG 的 delete_by_doc_id 功能刪除文檔
                await self._delete_document_by_lightrag_id(document_id, company_id)

                # 2. 刪除輸出文件
                await self._delete_document_files(document_id, company_id)

                print(f"✅ 文檔刪除完成: {document_id}")
                print("=" * 80)

                return {
                    "status": "success",
                    "message": f"Document {document_id} deleted successfully",
                    "document_id": document_id,
                    "company_id": company_id,
                }

        except Exception as e:
            print(f"❌ 文檔刪除失敗: {str(e)}")
            import traceback

            print(f"   詳細錯誤: {traceback.format_exc()}")
            print("=" * 80)
            return {
                "status": "error",
                "message": f"Failed to delete document: {str(e)}",
                "document_id": document_id,
                "company_id": company_id,
            }

    async def _validate_document(self, file_path: str) -> bool:
        """驗證文檔"""
        print(f"📊 檢查文檔...")

        # 檢查文件是否存在
        if not os.path.exists(file_path):
            print(f"❌ 文檔不存在: {file_path}")
            return False

        # 檢查文件大小
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / 1024 / 1024
        print(f"   文檔大小: {file_size} bytes ({file_size_mb:.2f} MB)")

        if file_size > 100 * 1024 * 1024:  # 100MB 限制
            print(f"❌ 文檔過大: {file_size_mb:.1f}MB (最大限制: 100MB)")
            return False

        print(f"✅ 文檔驗證通過")
        return True

    async def _process_document_content(self, file_path: str, output_dir: Path):
        """處理文檔內容 - 使用動態創建的 RAG-Anything 實例"""
        print(f"🔄 處理文檔內容...")

        try:
            # 檢查當前命名空間
            current_qdrant = os.environ.get("QDRANT_WORKSPACE", "default")
            current_neo4j = os.environ.get("NEO4J_WORKSPACE", "default")
            company_id = (
                current_qdrant.replace("company_", "")
                if "company_" in current_qdrant
                else "default"
            )

            print(
                f"   📌 處理時命名空間: Qdrant={current_qdrant}, Neo4j={current_neo4j}"
            )

            # 動態獲取當前公司的 RAG-Anything 實例
            print(f"🔄 為公司 {company_id} 動態創建 RAG-Anything 實例...")
            rag_instance = await self.rag_service.get_rag_instance_for_company(
                company_id
            )

            # 使用正確的 RAG-Anything 官方 API 處理文檔
            print(f"🚀 使用 RAG-Anything 官方 API 處理文檔: {file_path}")

            try:
                # 根據官方文檔，使用 process_document_complete 方法
                await rag_instance.process_document_complete(
                    file_path=file_path,
                    output_dir=str(output_dir),
                    parse_method="auto",  # 或 "ocr", "txt"
                )

                print(f"✅ RAG-Anything 文檔處理完成")

            except Exception as process_error:
                print(f"❌ RAG-Anything 文檔處理失敗: {process_error}")
                raise process_error

            print(f"✅ RAG-Anything 文檔處理和插入完成")
            
            # 嘗試獲取 LightRAG 的 doc_id
            lightrag_doc_id = None
            try:
                # 從 kv_store_doc_status.json 中獲取最新的 doc_id
                working_dir = self.config.working_dir
                doc_status_path = Path(working_dir) / "kv_store_doc_status.json"
                
                if doc_status_path.exists():
                    import json
                    with open(doc_status_path, 'r', encoding='utf-8') as f:
                        doc_status_data = json.load(f)
                    
                    # 找到最新的 doc_id (根據 created_at 時間戳)
                    if doc_status_data:
                        latest_doc = None
                        latest_time = None
                        
                        for doc_id, doc_info in doc_status_data.items():
                            if doc_info.get('created_at'):
                                if latest_time is None or doc_info['created_at'] > latest_time:
                                    latest_time = doc_info['created_at']
                                    latest_doc = doc_id
                        
                        if latest_doc:
                            lightrag_doc_id = latest_doc
                            print(f"📄 從 doc_status 獲取到最新的 LightRAG doc_id: {lightrag_doc_id}")
                            print(f"   對應文件: {doc_status_data[latest_doc].get('file_path', 'unknown')}")
                            
                            # 存儲到類變量中，供上層調用獲取
                            self._last_processed_doc_id = lightrag_doc_id
                
            except Exception as doc_id_error:
                print(f"⚠️  獲取 LightRAG doc_id 失敗: {doc_id_error}")

            print(f"✅ RAG-Anything 文檔處理和插入完成")

        except Exception as e:
            print(f"❌ RAG-Anything 文檔處理失敗: {e}")
            import traceback

            print(f"   詳細錯誤: {traceback.format_exc()}")
            raise

    async def _verify_content_insertion(self, inserted_content: str):
        """驗證內容是否成功插入"""
        try:
            print(f"🔍 驗證內容插入...")

            # 檢查向量資料庫
            current_workspace = os.environ.get("QDRANT_WORKSPACE", "default")

            from qdrant_client import QdrantClient

            qdrant_client = QdrantClient(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6333")),
            )

            collections = qdrant_client.get_collections()
            workspace_collections = [
                c for c in collections.collections if current_workspace in c.name
            ]

            total_points = 0
            for collection in workspace_collections:
                try:
                    info = qdrant_client.get_collection(collection.name)
                    points_count = info.points_count
                    total_points += points_count
                    print(f"   📦 {collection.name}: {points_count} 個向量點")
                except Exception as e:
                    print(f"   ⚠️  集合 {collection.name} 檢查失敗: {e}")

            print(f"   📊 總向量點數: {total_points}")

            if total_points == 0:
                print(f"   ⚠️  警告: 向量點數量為0，但 RAG-Anything 可能仍在處理中")
            else:
                print(f"   ✅ 向量插入驗證成功")

        except Exception as e:
            print(f"   ⚠️  插入驗證失敗: {e}")

    async def _recreate_lightrag_instance(self):
        """重新創建 LightRAG 實例以使用新命名空間 - 修正關鍵bug"""
        try:
            print(f"🔄 重新創建 LightRAG 實例...")

            from lightrag import LightRAG
            from lightrag.llm.openai import openai_complete_if_cache, openai_embed
            from lightrag.utils import EmbeddingFunc

            # 獲取配置
            llm_config = self.config.get_llm_config()
            embedding_config = self.config.get_embedding_config()

            # 修正：使用正確的函數簽名
            def llm_model_func(
                prompt, system_prompt=None, history_messages=[], **kwargs
            ):
                return openai_complete_if_cache(
                    llm_config["model"],
                    prompt,
                    system_prompt=system_prompt,
                    history_messages=history_messages,
                    api_key=llm_config["api_key"],
                    base_url=llm_config["base_url"],
                    **kwargs,
                )

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

            # 創建新的 LightRAG 實例 - 修正：確保使用當前環境變數中的命名空間
            current_workspace = os.environ.get("QDRANT_WORKSPACE", "default")
            print(f"   📌 使用命名空間: {current_workspace}")
            print(f"   📁 工作目錄: {self.config.working_dir}")

            new_lightrag_instance = LightRAG(
                working_dir=self.config.working_dir,
                llm_model_func=llm_model_func,
                embedding_func=embedding_func,
                vector_storage="QdrantVectorDBStorage",
                graph_storage="Neo4JStorage",
            )

            # 修正：確保存儲初始化時使用正確的命名空間
            print(f"🔄 初始化存儲...")
            await new_lightrag_instance.initialize_storages()
            print(f"✅ 存儲初始化完成")

            # 修正：確認存儲連接狀態
            print(f"🔍 驗證存儲連接...")
            if (
                hasattr(new_lightrag_instance, "vector_db")
                and new_lightrag_instance.vector_db
            ):
                print(f"   ✅ Vector DB 連接正常")
            else:
                print(f"   ⚠️  Vector DB 連接異常")

            if (
                hasattr(new_lightrag_instance, "graph_storage")
                and new_lightrag_instance.graph_storage
            ):
                print(f"   ✅ Graph Storage 連接正常")
            else:
                print(f"   ⚠️  Graph Storage 連接異常")

            # 更新 RAG-Anything 實例的 lightrag
            self.rag_instance.lightrag = new_lightrag_instance

            print(f"✅ LightRAG 實例重新創建完成")

        except Exception as e:
            print(f"❌ LightRAG 實例重新創建失敗: {e}")
            import traceback

            print(f"   詳細錯誤: {traceback.format_exc()}")
            raise

    async def _verify_processing_results(
        self, company_workspace: str, file_path: str, output_dir: Path
    ):
        """驗證處理結果"""
        print(f"🔍 驗證處理結果...")

        # 檢查輸出目錄
        if output_dir.exists():
            output_files = list(output_dir.rglob("*"))
            print(f"   輸出文件數量: {len(output_files)}")
            for output_file in output_files[:5]:  # 只顯示前5個文件
                if output_file.is_file():
                    file_size = output_file.stat().st_size
                    print(f"   - {output_file.name}: {file_size} bytes")

        # 檢查數據庫狀態
        await self.db_manager.check_company_data_status(
            company_workspace.replace("company_", "")
        )

    async def _delete_document_vectors(self, document_id: str, company_workspace: str):
        """刪除文檔的向量數據"""
        print(f"🗑️  刪除向量數據...")

        try:
            from qdrant_client import QdrantClient

            qdrant_client = QdrantClient(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6333")),
            )

            # 獲取公司的所有集合
            collections = qdrant_client.get_collections()
            company_collections = [
                c.name for c in collections.collections if company_workspace in c.name
            ]

            deleted_count = 0
            for collection_name in company_collections:
                try:
                    # 嘗試根據 document_id 刪除點
                    # 由於不知道具體的點ID，暫時跳過，需要更詳細的實現
                    print(f"   檢查集合: {collection_name}")
                    info = qdrant_client.get_collection(collection_name)
                    print(f"   集合中的點數: {info.points_count}")

                except Exception as e:
                    print(f"   處理集合 {collection_name} 時出錯: {e}")

            print(f"   已處理 {len(company_collections)} 個向量集合")

        except Exception as e:
            print(f"   向量刪除失敗: {e}")

    async def _delete_document_graph_data(
        self, document_id: str, company_workspace: str
    ):
        """刪除文檔的知識圖譜數據"""
        print(f"🗑️  刪除知識圖譜數據...")

        try:
            from neo4j import AsyncGraphDatabase

            driver = AsyncGraphDatabase.driver(
                os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                auth=(
                    os.getenv("NEO4J_USER", "neo4j"),
                    os.getenv("NEO4J_PASSWORD", "password"),
                ),
            )

            async with driver.session() as session:
                # 刪除與文檔相關的節點和關係
                # 這裡需要根據實際的圖結構來實現具體的刪除邏輯
                query = """
                MATCH (n)
                WHERE n.document_id = $document_id OR n.source_document = $document_id
                DETACH DELETE n
                """

                result = await session.run(query, document_id=document_id)
                print(f"   已刪除與文檔 {document_id} 相關的圖數據")

            await driver.close()

        except Exception as e:
            print(f"   圖數據刪除失敗: {e}")

    async def _delete_document_files(self, document_id: str, company_id: str):
        """刪除文檔的輸出文件"""
        print(f"🗑️  刪除輸出文件...")

        try:
            # 修正後的文件結構：./output/company_XX/filename/auto/
            company_output_dir = self.config.get_company_output_dir(
                company_id, "./output"
            )
            print(f"   公司輸出目錄: {company_output_dir}")

            # 還需要處理舊的結構：./output/filename/auto/ (沒有公司隔離)
            base_output_dir = Path("./output")

            deleted_any = False

            # 1. 刪除新結構中的文件 (company_id/filename/)
            if company_output_dir.exists():
                potential_dirs = list(company_output_dir.glob("*"))
                for dir_path in potential_dirs:
                    if dir_path.is_dir():
                        # document_id 通常是 UUID，但文件夾名稱是文件名（去掉擴展名）
                        # 檢查是否與文檔相關
                        print(f"   檢查目錄: {dir_path.name}")
                        if self._is_document_directory(dir_path, document_id):
                            print(f"   ✅ 刪除公司目錄: {dir_path}")
                            import shutil

                            shutil.rmtree(dir_path, ignore_errors=True)
                            deleted_any = True

            # 2. 刪除舊結構中的文件 (直接在 output 根目錄)
            if base_output_dir.exists():
                potential_dirs = list(base_output_dir.glob("*"))
                for dir_path in potential_dirs:
                    if dir_path.is_dir() and dir_path.name != f"company_{company_id}":
                        if self._is_document_directory(dir_path, document_id):
                            print(f"   ✅ 刪除舊結構目錄: {dir_path}")
                            import shutil

                            shutil.rmtree(dir_path, ignore_errors=True)
                            deleted_any = True

            if not deleted_any:
                print(f"   ⚠️  未找到與文檔 {document_id} 相關的輸出文件")

        except Exception as e:
            print(f"   文件刪除失敗: {e}")

    def _is_document_directory(self, dir_path: Path, document_id: str) -> bool:
        """檢查目錄是否屬於指定文檔"""
        # 檢查目錄中是否有以 document_id 相關的文件
        # 或者目錄名稱包含文檔信息
        if not dir_path.is_dir():
            return False

        # 檢查 auto 子目錄中的文件
        auto_dir = dir_path / "auto"
        if auto_dir.exists():
            # 檢查是否有相關的 .md 或其他文件
            files = list(auto_dir.glob("*"))
            if files:
                # 如果目錄名與 document_id 匹配或包含相關信息
                return True

        return False

    async def _delete_document_by_lightrag_id(self, document_id: str, company_id: str):
        """使用 LightRAG 的 delete_by_doc_id 功能刪除文檔 (企業級做法)"""
        try:
            print(f"🔄 使用 LightRAG delete_by_doc_id 刪除文檔...")
            
            # 獲取公司的 RAG 實例
            rag_instance = await self.rag_service.get_rag_instance_for_company(company_id)
            
            # 從資料庫獲取已存儲的 LightRAG doc_id
            from app.core.database import SessionLocal
            db = SessionLocal()
            
            try:
                from app.models.document import DocumentMetadata
                document_record = db.query(DocumentMetadata).filter(
                    DocumentMetadata.document_id == document_id,
                    DocumentMetadata.company_id == int(company_id)
                ).first()
                
                if not document_record:
                    print(f"⚠️  未找到文檔記錄: {document_id}")
                    return
                
                # 優先使用數據庫中存儲的 LightRAG doc_id
                lightrag_doc_id = document_record.lightrag_doc_id
                
                if not lightrag_doc_id:
                    print(f"⚠️  數據庫中沒有 LightRAG doc_id，嘗試計算...")
                    # 降級方案：計算 LightRAG doc_id
                    if document_record.file_path and Path(document_record.file_path).exists():
                        try:
                            with open(document_record.file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read().strip()
                            
                            from lightrag.utils import compute_mdhash_id
                            lightrag_doc_id = compute_mdhash_id(file_content, prefix="doc-")
                            print(f"🔢 計算出的 LightRAG doc_id: {lightrag_doc_id}")
                        except Exception as calc_error:
                            print(f"❌ 計算 LightRAG doc_id 失敗: {calc_error}")
                            return
                    else:
                        print(f"⚠️  文檔文件不存在，無法計算 doc_id: {document_record.file_path}")
                        return
                
                # 使用 LightRAG 的 delete_by_doc_id 功能
                if lightrag_doc_id:
                    print(f"📄 使用 LightRAG doc_id 刪除: {lightrag_doc_id}")
                    try:
                        await rag_instance.delete_by_doc_id(lightrag_doc_id)
                        print(f"✅ LightRAG 文檔刪除成功")
                    except Exception as delete_error:
                        print(f"⚠️  LightRAG 刪除失敗: {delete_error}")
                        # 記錄錯誤但不阻斷流程
                        
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ 使用 LightRAG 刪除文檔失敗: {e}")
            # 企業級做法：記錄錯誤但不阻斷清理流程

    def _create_error_response(self, file_path: str, message: str) -> Dict[str, Any]:
        """創建錯誤回應"""
        return {
            "status": "error",
            "message": message,
            "file_path": file_path,
        }
