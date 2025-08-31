"""
多租戶 RAG-Anything 服務管理器 - 新獨立文件夾架構版本
"""

import os
import asyncio
import psutil
import threading
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from app.services.rag_anything import RAGAnythingService
from app.models.company import Company
from sqlalchemy.orm import Session


class ResourceManager:
    """資源管理器 - 適配獨立文件夾架構"""

    def __init__(self):
        self.company_memory_usage = {}
        self.max_memory_per_company = (
            int(os.getenv("MAX_MEMORY_PER_COMPANY_MB", "500")) * 1024 * 1024
        )  # 預設 500MB
        self.max_storage_per_company = (
            int(os.getenv("MAX_STORAGE_PER_COMPANY_GB", "1")) * 1024 * 1024 * 1024
        )  # 預設 1GB
        self.max_documents_per_company = int(
            os.getenv("MAX_DOCUMENTS_PER_COMPANY", "100")
        )  # 預設 100個文檔
        self._lock = threading.Lock()

    async def check_memory_usage(self, company_id: int) -> Dict[str, Any]:
        """檢查公司記憶體使用量"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            # 估算每個公司的記憶體使用量
            total_companies = len(self.company_memory_usage) or 1
            estimated_memory_per_company = memory_info.rss // total_companies

            usage_percent = (
                estimated_memory_per_company / self.max_memory_per_company
            ) * 100

            result = {
                "company_id": company_id,
                "memory_usage": estimated_memory_per_company,
                "memory_limit": self.max_memory_per_company,
                "usage_percent": usage_percent,
                "status": (
                    "ok"
                    if usage_percent < 80
                    else "warning" if usage_percent < 95 else "critical"
                ),
            }

            if usage_percent > 80:
                print(
                    f"⚠️ 公司 {company_id} 記憶體使用率: {usage_percent:.1f}% ({estimated_memory_per_company / 1024 / 1024:.0f}MB)"
                )

            return result

        except Exception as e:
            print(f"❌ 檢查記憶體使用量失敗: {e}")
            return {"status": "error", "message": str(e)}

    async def check_storage_usage(self, company_id: int) -> Dict[str, Any]:
        """檢查公司儲存使用量 - 適配獨立文件夾架構"""
        try:
            # 使用新的獨立文件夾路徑結構
            company_dir = Path(f"./rag_storage/company_{company_id}")

            if not company_dir.exists():
                return {
                    "company_id": company_id,
                    "storage_usage": 0,
                    "storage_limit": self.max_storage_per_company,
                    "usage_percent": 0,
                    "document_count": 0,
                    "status": "ok",
                }

            total_size = 0
            document_count = 0

            document_folders = []

            # 遍歷所有文檔文件夾（只計算以 doc- 開頭的文件夾）
            for doc_folder in company_dir.iterdir():
                if doc_folder.is_dir() and doc_folder.name.startswith('doc-'):
                    folder_size = 0
                    # 計算文件夾大小
                    for file_path in doc_folder.rglob("*"):
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            folder_size += file_size
                            total_size += file_size
                    
                    if folder_size > 0:  # 只計算非空文件夾
                        document_count += 1
                        document_folders.append({
                            "doc_id": doc_folder.name,
                            "size": folder_size,
                            "size_mb": folder_size / 1024 / 1024,
                            "files": len([f for f in doc_folder.rglob("*") if f.is_file()])
                        })

            usage_percent = (total_size / self.max_storage_per_company) * 100

            result = {
                "company_id": company_id,
                "storage_usage": total_size,
                "storage_limit": self.max_storage_per_company,
                "usage_percent": usage_percent,
                "document_count": document_count,
                "document_folders": document_folders,
                "storage_usage_mb": total_size / 1024 / 1024,
                "storage_limit_mb": self.max_storage_per_company / 1024 / 1024,
                "status": (
                    "ok"
                    if usage_percent < 80
                    else "warning" if usage_percent < 95 else "critical"
                ),
            }

            if usage_percent > 80:
                print(
                    f"⚠️ 公司 {company_id} 儲存使用率: {usage_percent:.1f}% ({total_size / 1024 / 1024:.1f}MB, {document_count} 個文檔)"
                )
            
            print(f"📊 公司 {company_id} 儲存情況: {document_count} 個文檔, {total_size / 1024 / 1024:.1f}MB")

            return result

        except Exception as e:
            print(f"❌ 檢查儲存配額失敗: {e}")
            return {"status": "error", "message": str(e)}

    async def check_document_limit(self, company_id: int) -> Dict[str, Any]:
        """檢查公司文檔數量限制"""
        try:
            company_dir = Path(f"./rag_storage/company_{company_id}")

            if not company_dir.exists():
                document_count = 0
            else:
                document_count = len([f for f in company_dir.iterdir() if f.is_dir() and f.name.startswith('doc-')])

            usage_percent = (document_count / self.max_documents_per_company) * 100

            result = {
                "company_id": company_id,
                "document_count": document_count,
                "document_limit": self.max_documents_per_company,
                "usage_percent": usage_percent,
                "status": (
                    "ok"
                    if usage_percent < 80
                    else "warning" if usage_percent < 95 else "critical"
                ),
            }

            if usage_percent > 80:
                print(
                    f"⚠️ 公司 {company_id} 文檔數量: {document_count}/{self.max_documents_per_company} ({usage_percent:.1f}%)"
                )

            return result

        except Exception as e:
            print(f"❌ 檢查文檔限制失敗: {e}")
            return {"status": "error", "message": str(e)}

    async def cleanup_old_documents(
        self, company_id: int, days_old: int = 30
    ) -> Dict[str, Any]:
        """清理舊文檔 - 基於獨立文件夾架構的原子刪除"""
        try:
            from datetime import datetime, timedelta

            company_dir = Path(f"./rag_storage/company_{company_id}")
            if not company_dir.exists():
                return {"status": "ok", "message": "目錄不存在"}

            cutoff_date = datetime.now() - timedelta(days=days_old)

            cleaned_documents = 0
            freed_space = 0

            # 遍歷所有文檔文件夾
            for doc_folder in company_dir.iterdir():
                if doc_folder.is_dir():
                    try:
                        # 檢查文件夾的修改時間
                        folder_mtime = datetime.fromtimestamp(
                            doc_folder.stat().st_mtime
                        )
                        if folder_mtime < cutoff_date:
                            # 計算文件夾大小（用於統計）
                            folder_size = sum(
                                f.stat().st_size
                                for f in doc_folder.rglob("*")
                                if f.is_file()
                            )

                            # 原子刪除整個文件夾
                            shutil.rmtree(doc_folder)
                            cleaned_documents += 1
                            freed_space += folder_size

                            print(f"🗑️ 已刪除舊文檔文件夾: {doc_folder.name}")

                    except OSError as e:
                        print(f"⚠️ 刪除文檔文件夾失敗 {doc_folder.name}: {e}")

            result = {
                "company_id": company_id,
                "cleaned_documents": cleaned_documents,
                "freed_space": freed_space,
                "freed_space_mb": freed_space / 1024 / 1024,
                "status": "ok",
            }

            if cleaned_documents > 0:
                print(
                    f"🧹 公司 {company_id} 清理了 {cleaned_documents} 個舊文檔，釋放 {freed_space / 1024 / 1024:.1f}MB 空間"
                )

            return result

        except Exception as e:
            print(f"❌ 清理舊文檔失敗: {e}")
            return {"status": "error", "message": str(e)}


class MultiTenantRAGService:
    """多租戶 RAG 服務管理器 - 新獨立文件夾架構版本"""

    def __init__(self):
        self.tenant_services: Dict[int, RAGAnythingService] = {}
        self.processing_pools: Dict[int, ThreadPoolExecutor] = {}
        self.resource_manager = ResourceManager()

    async def get_company_rag_service(
        self, company_id: int, db: Session
    ) -> RAGAnythingService:
        """取得指定公司的 RAG 服務實例"""

        # 如果已經初始化過，直接回傳
        if company_id in self.tenant_services:
            return self.tenant_services[company_id]

        # 從資料庫取得公司資訊
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company {company_id} not found")

        if not company.is_active:
            raise ValueError(f"Company {company_id} is not active")

        # 建立公司專用的 RAG 服務
        rag_service = RAGAnythingService(company_id=str(company_id))

        # 初始化服務
        await rag_service.initialize(str(company_id))

        # 快取服務實例
        self.tenant_services[company_id] = rag_service

        return rag_service

    async def process_document_async(
        self, company_id: int, file_path: str, db: Session
    ) -> Dict[str, Any]:
        """異步文檔處理 - 適配獨立文件夾架構"""

        print(f"🚀 開始異步文檔處理 - 公司ID: {company_id}, 文件: {file_path}")

        # 檢查資源限制
        storage_check = await self.resource_manager.check_storage_usage(company_id)
        if storage_check["status"] == "critical":
            return {
                "status": "error",
                "message": f"公司 {company_id} 儲存空間不足 ({storage_check['usage_percent']:.1f}%)",
                "file_path": file_path,
            }

        doc_limit_check = await self.resource_manager.check_document_limit(company_id)
        if doc_limit_check["status"] == "critical":
            return {
                "status": "error",
                "message": f"公司 {company_id} 文檔數量已達上限 ({doc_limit_check['document_count']}/{doc_limit_check['document_limit']})",
                "file_path": file_path,
            }

        # 確保公司有專用的處理線程池
        if company_id not in self.processing_pools:
            self.processing_pools[company_id] = ThreadPoolExecutor(
                max_workers=1, thread_name_prefix=f"company_{company_id}_processor"
            )

        # 獲取公司專用的 RAG 服務
        rag_service = await self.get_company_rag_service(company_id, db)

        try:
            # 檢查快取（如果實現了）
            cache_result = await rag_service.process_document_with_cache(
                file_path, str(company_id)
            )
            if cache_result.get("status") == "hit":
                return {**cache_result, "status": "success", "cache": True}

            # 在線程池中執行處理
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.processing_pools[company_id],
                self._process_document_sync,
                rag_service,
                file_path,
                str(company_id),
            )

            # 確保結果包含必要的字段
            if result.get("status") == "success" and "doc_id" in result:
                print(
                    f"✅ 文檔處理成功 - 公司: {company_id}, 文檔ID: {result['doc_id']}"
                )
                return result
            else:
                # 如果處理失敗，返回錯誤
                return {
                    "status": "error",
                    "message": f"文檔處理失敗: {result.get('message', '未知錯誤')}",
                    "file_path": file_path,
                    "result": result,
                }

        except Exception as e:
            print(f"❌ 異步文檔處理失敗 - 公司ID: {company_id}, 錯誤: {e}")
            return {
                "status": "error",
                "message": f"文檔處理失敗: {str(e)}",
                "file_path": file_path,
            }

    def _process_document_sync(
        self, rag_service, file_path: str, company_id: str
    ) -> Dict[str, Any]:
        """在線程池中執行的同步文檔處理"""
        import threading

        print(f"🔄 在線程池中執行文檔處理 - 線程ID: {threading.current_thread().name}")

        try:
            # 創建新的事件循環來執行異步處理
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    rag_service.process_document(file_path, int(company_id))
                )
                print("✅ 線程池文檔處理成功")
                return result
            finally:
                loop.close()

        except Exception as e:
            print(f"❌ 線程池文檔處理失敗: {e}")
            import traceback

            traceback.print_exc()
            return {"status": "error", "message": str(e), "file_path": file_path}

    async def delete_document_async(
        self, company_id: int, document_id: str, db: Session
    ) -> Dict[str, Any]:
        """異步文檔刪除 - 基於獨立文件夾架構的原子刪除"""

        print(f"🗑️ 開始異步文檔刪除 - 公司ID: {company_id}, 文檔ID: {document_id}")

        # 檢查文檔是否存在
        company_dir = Path(f"./rag_storage/company_{company_id}")
        doc_folder = company_dir / document_id

        if not doc_folder.exists():
            return {
                "status": "error",
                "message": f"文檔 {document_id} 不存在",
                "document_id": document_id,
            }

        # 獲取公司專用的 RAG 服務
        rag_service = await self.get_company_rag_service(company_id, db)

        try:
            # 原子刪除文檔文件夾
            import shutil

            # 計算文件夾大小（用於統計）
            folder_size = sum(
                f.stat().st_size for f in doc_folder.rglob("*") if f.is_file()
            )

            # 刪除整個文件夾
            shutil.rmtree(doc_folder)

            result = {
                "status": "success",
                "message": f"文檔 {document_id} 已成功刪除",
                "document_id": document_id,
                "company_id": company_id,
                "freed_space": folder_size,
                "freed_space_mb": folder_size / 1024 / 1024,
            }

            print(
                f"✅ 文檔刪除成功 - 公司: {company_id}, 文檔ID: {document_id}, 釋放空間: {folder_size / 1024 / 1024:.1f}MB"
            )
            return result

        except Exception as e:
            print(
                f"❌ 文檔刪除失敗 - 公司ID: {company_id}, 文檔ID: {document_id}, 錯誤: {e}"
            )
            return {
                "status": "error",
                "message": f"文檔刪除失敗: {str(e)}",
                "document_id": document_id,
            }

    async def query_documents_async(
        self, company_id: int, query: str, db: Session, **kwargs
    ) -> Dict[str, Any]:
        """異步文檔查詢 - 基於獨立文件夾架構"""

        print(f"🔍 開始異步文檔查詢 - 公司ID: {company_id}, 查詢: {query[:50]}...")

        # 檢查資源使用情況
        memory_check = await self.resource_manager.check_memory_usage(company_id)
        if memory_check["status"] == "critical":
            return {
                "status": "error",
                "message": f"公司 {company_id} 記憶體使用率過高 ({memory_check['usage_percent']:.1f}%)",
                "query": query,
            }

        # 獲取公司專用的 RAG 服務
        rag_service = await self.get_company_rag_service(company_id, db)

        try:
            # 執行查詢
            result = await rag_service.query_documents(query, str(company_id), **kwargs)

            print(
                f"✅ 文檔查詢成功 - 公司: {company_id}, 結果數量: {len(result.get('results', []))}"
            )
            return result

        except Exception as e:
            print(f"❌ 文檔查詢失敗 - 公司ID: {company_id}, 錯誤: {e}")
            return {
                "status": "error",
                "message": f"文檔查詢失敗: {str(e)}",
                "query": query,
            }

    async def get_company_stats(self, company_id: int) -> Dict[str, Any]:
        """取得公司統計資訊"""

        try:
            # 並發檢查各項資源使用情況
            storage_task = self.resource_manager.check_storage_usage(company_id)
            memory_task = self.resource_manager.check_memory_usage(company_id)
            doc_limit_task = self.resource_manager.check_document_limit(company_id)

            storage_result, memory_result, doc_limit_result = await asyncio.gather(
                storage_task, memory_task, doc_limit_task
            )

            # 計算總體健康狀態
            statuses = [
                storage_result["status"],
                memory_result["status"],
                doc_limit_result["status"],
            ]

            # 確定最差的狀態
            status_priority = {"ok": 0, "warning": 1, "critical": 2, "error": 3}
            worst_status = max(statuses, key=lambda s: status_priority.get(s, 0))

            stats = {
                "company_id": company_id,
                "status": worst_status,
                "storage": storage_result,
                "memory": memory_result,
                "documents": doc_limit_result,
                "timestamp": asyncio.get_event_loop().time(),
            }

            return stats

        except Exception as e:
            print(f"❌ 取得公司統計失敗: {e}")
            return {
                "company_id": company_id,
                "status": "error",
                "message": str(e),
            }

    async def cleanup_company_data(
        self, company_id: int, days_old: int = 30
    ) -> Dict[str, Any]:
        """清理公司舊資料"""

        print(f"🧹 開始清理公司 {company_id} 的舊資料...")

        try:
            result = await self.resource_manager.cleanup_old_documents(
                company_id, days_old
            )

            if result["status"] == "ok":
                print(f"✅ 公司 {company_id} 資料清理完成")
            else:
                print(
                    f"❌ 公司 {company_id} 資料清理失敗: {result.get('message', '未知錯誤')}"
                )

            return result

        except Exception as e:
            print(f"❌ 清理公司資料失敗: {e}")
            return {
                "company_id": company_id,
                "status": "error",
                "message": str(e),
            }


# 全域實例
_multitenant_service = None


def get_multitenant_rag_service() -> MultiTenantRAGService:
    """取得多租戶 RAG 服務實例"""
    global _multitenant_service
    if _multitenant_service is None:
        _multitenant_service = MultiTenantRAGService()
    return _multitenant_service


# 全域實例
_multitenant_service = None


def get_multitenant_rag_service() -> MultiTenantRAGService:
    """取得多租戶 RAG 服務實例"""
    global _multitenant_service
    if _multitenant_service is None:
        _multitenant_service = MultiTenantRAGService()
    return _multitenant_service
