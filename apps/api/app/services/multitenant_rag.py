"""
多租戶 RAG-Anything 服務管理器
"""

import os
import asyncio
import psutil
import threading
from typing import Dict, List, Optional, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from app.services.rag_anything import RAGAnythingService
from app.models.company import Company
from sqlalchemy.orm import Session


class ResourceManager:
    """資源管理器"""

    def __init__(self):
        self.company_memory_usage = {}
        self.max_memory_per_company = (
            int(os.getenv("MAX_MEMORY_PER_COMPANY_MB", "500")) * 1024 * 1024
        )  # 預設 500MB
        self.max_storage_per_company = (
            int(os.getenv("MAX_STORAGE_PER_COMPANY_GB", "1")) * 1024 * 1024 * 1024
        )  # 預設 1GB
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

            with self._lock:
                self.company_memory_usage[company_id] = estimated_memory_per_company

            if usage_percent > 80:
                print(
                    f"⚠️ 公司 {company_id} 記憶體使用率: {usage_percent:.1f}% ({estimated_memory_per_company / 1024 / 1024:.1f}MB)"
                )

            return result

        except Exception as e:
            print(f"❌ 檢查記憶體使用量失敗: {e}")
            return {"status": "error", "message": str(e)}

    async def check_storage_quota(self, company_id: int) -> Dict[str, Any]:
        """檢查公司儲存配額"""
        try:
            company_dir = f"./rag_storage/company_{company_id}"

            if not os.path.exists(company_dir):
                return {
                    "company_id": company_id,
                    "storage_usage": 0,
                    "storage_limit": self.max_storage_per_company,
                    "usage_percent": 0.0,
                    "status": "ok",
                }

            # 計算目錄總大小
            total_size = 0
            file_count = 0

            for dirpath, dirnames, filenames in os.walk(company_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                        file_count += 1
                    except OSError:
                        pass

            usage_percent = (total_size / self.max_storage_per_company) * 100

            result = {
                "company_id": company_id,
                "storage_usage": total_size,
                "storage_limit": self.max_storage_per_company,
                "usage_percent": usage_percent,
                "file_count": file_count,
                "status": (
                    "ok"
                    if usage_percent < 80
                    else "warning" if usage_percent < 95 else "critical"
                ),
            }

            if usage_percent > 80:
                print(
                    f"⚠️ 公司 {company_id} 儲存使用率: {usage_percent:.1f}% ({total_size / 1024 / 1024 / 1024:.2f}GB, {file_count} 檔案)"
                )

            return result

        except Exception as e:
            print(f"❌ 檢查儲存配額失敗: {e}")
            return {"status": "error", "message": str(e)}

    async def cleanup_old_data(
        self, company_id: int, days_old: int = 30
    ) -> Dict[str, Any]:
        """清理舊資料"""
        try:
            from datetime import datetime, timedelta

            company_dir = f"./rag_storage/company_{company_id}"
            if not os.path.exists(company_dir):
                return {"status": "ok", "message": "目錄不存在"}

            cutoff_date = datetime.now() - timedelta(days=days_old)

            cleaned_files = 0
            freed_space = 0

            for dirpath, dirnames, filenames in os.walk(company_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        if file_mtime < cutoff_date:
                            size = os.path.getsize(filepath)
                            os.remove(filepath)
                            cleaned_files += 1
                            freed_space += size
                    except OSError:
                        pass

            result = {
                "company_id": company_id,
                "cleaned_files": cleaned_files,
                "freed_space": freed_space,
                "freed_space_mb": freed_space / 1024 / 1024,
                "status": "ok",
            }

            if cleaned_files > 0:
                print(
                    f"🧹 公司 {company_id} 清理了 {cleaned_files} 個舊檔案，釋放 {freed_space / 1024 / 1024:.1f}MB 空間"
                )

            return result

        except Exception as e:
            print(f"❌ 清理舊資料失敗: {e}")
            return {"status": "error", "message": str(e)}


class MultiTenantRAGService:
    """多租戶 RAG 服務管理器"""

    def __init__(self):
        self.tenant_services: Dict[int, RAGAnythingService] = {}
        # 新增：文檔處理線程池（每個公司隔離）
        self.processing_pools: Dict[int, ThreadPoolExecutor] = {}
        # 新增：資源管理器
        self.resource_manager = ResourceManager()

    def clear_all_caches(self):
        """清空所有緩存，防止舊狀態干擾伺服器啟動"""
        print("🧹 清空多租戶 RAG 服務緩存")
        self.tenant_services.clear()

        # 清理線程池
        for company_id, pool in self.processing_pools.items():
            pool.shutdown(wait=False)
        self.processing_pools.clear()

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

        # 建立公司專用的 RAG 服務，傳入 company_id
        rag_service = RAGAnythingService(company_id=str(company_id))

        # 設定基礎目錄，讓 rag_config.py 自動處理公司ID
        os.environ["RAG_WORKING_DIR"] = "./rag_storage"

        # 確保公司目錄存在
        working_dir = f"./rag_storage/company_{company_id}"
        Path(working_dir).mkdir(parents=True, exist_ok=True)

        # 初始化服務，傳入 company_id
        await rag_service.initialize(company_id=str(company_id))

        # 快取服務實例
        self.tenant_services[company_id] = rag_service

        return rag_service

    async def process_document_async(
        self, company_id: int, file_path: str, db: Session
    ) -> Dict[str, Any]:
        """異步文檔處理 - 維持多租戶隔離，解決 MinerU 阻塞問題"""

        print(f"🚀 開始異步文檔處理 - 公司ID: {company_id}, 文件: {file_path}")

        # 確保公司有專用的處理線程池
        if company_id not in self.processing_pools:
            self.processing_pools[company_id] = ThreadPoolExecutor(
                max_workers=1, thread_name_prefix=f"company_{company_id}_processor"
            )
            print(f"📦 為公司 {company_id} 創建專用線程池")

        # 獲取公司專用的 RAG 服務
        rag_service = await self.get_company_rag_service(company_id, db)

        # 在公司專用線程池中執行文檔處理
        loop = asyncio.get_event_loop()

        print(f"⚡ 將 MinerU 處理移到線程池，避免阻塞主事件循環")

        try:
            # 先嘗試 parse cache（非阻塞，仍在主 loop）
            cache_result = await rag_service.process_document_with_cache(
                file_path, str(company_id)
            )
            if cache_result.get("status") == "hit":
                return {**cache_result, "status": "success", "cache": True}

            # 生成處理任務ID
            import uuid
            task_id = str(uuid.uuid4())
            
            # 非阻塞啟動背景處理任務
            print(f"🚀 啟動非阻塞背景處理任務: {task_id}")
            asyncio.create_task(
                self._process_document_background(
                    task_id, rag_service, file_path, str(company_id)
                )
            )

            # 立即返回，不等待處理完成
            return {
                "status": "processing",
                "message": "文檔處理已在背景啟動",
                "task_id": task_id,
                "file_path": file_path,
                "company_id": company_id
            }

        except Exception as e:
            print(f"❌ 異步文檔處理失敗 - 公司ID: {company_id}, 錯誤: {e}")
            return {
                "status": "error",
                "message": f"Document processing failed: {str(e)}",
                "file_path": file_path,
            }

    def _process_document_sync(
        self, rag_service, file_path: str, company_id: str
    ) -> Dict[str, Any]:
        """在線程池中執行的純同步文檔處理 - 避免事件循環問題"""
        import threading

        print(
            f"🔄 在線程池中執行純同步文檔處理 - 線程ID: {threading.current_thread().name}"
        )

        try:
            # 直接調用同步版本，避免事件循環問題
            print(f"🎯 調用同步文檔處理方法")

            # 這裡需要調用 RAG 服務的同步處理方法
            # 由於 process_document 是異步的，我們需要在這個線程中創建事件循環
            import asyncio

            # 創建新的事件循環
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    rag_service.process_document(file_path, company_id)
                )
                print(f"✅ 線程池文檔處理成功")
                return result
            finally:
                # 簡單清理：直接關閉循環
                try:
                    loop.close()
                except:
                    pass

        except Exception as e:
            print(f"❌ 線程池文檔處理失敗: {e}")
            import traceback
            
    async def _process_document_background(self, task_id: str, rag_service, file_path: str, company_id: str):
        """真正的背景處理任務 - 不阻塞主事件循環"""
        try:
            print(f"🔄 背景任務 {task_id} 開始處理文檔: {file_path}")
            
            # 在線程池中執行處理
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.processing_pools[int(company_id)],
                self._process_document_sync,
                rag_service,
                file_path,
                company_id,
            )
            
            print(f"✅ 背景任務 {task_id} 處理完成")
            # 這裡可以更新數據庫狀態、發送通知等
            
        except Exception as e:
            print(f"❌ 背景任務 {task_id} 處理失敗: {e}")
            import traceback

            traceback.print_exc()
            return {"status": "error", "message": str(e), "file_path": file_path}

    async def get_company_by_line_channel(
        self, channel_token: str, db: Session
    ) -> Optional[Company]:
        """根據 LINE Channel Token 找到對應的公司"""
        return (
            db.query(Company)
            .filter(
                Company.line_channel_token == channel_token, Company.is_active == True
            )
            .first()
        )

    async def cleanup_company_service(self, company_id: int):
        """清理指定公司的 RAG 服務"""
        if company_id in self.tenant_services:
            # 這裡可以加入清理邏輯
            del self.tenant_services[company_id]

        # 清理線程池
        if company_id in self.processing_pools:
            self.processing_pools[company_id].shutdown(wait=True)
            del self.processing_pools[company_id]
            print(f"🧹 已清理公司 {company_id} 的處理線程池")

    async def cleanup_all_services(self):
        """清理所有 RAG 服務"""
        for company_id in list(self.tenant_services.keys()):
            await self.cleanup_company_service(company_id)

    async def check_company_quota(self, company_id: int, db: Session) -> Dict[str, any]:
        """檢查公司配額限制（完整實作）"""
        try:
            # 檢查文檔數量限制
            from app.models.document import Document

            doc_count = (
                db.query(Document).filter(Document.company_id == company_id).count()
            )

            max_documents = 1000  # 預設限制
            doc_usage_percent = (doc_count / max_documents) * 100

            # 檢查存儲空間使用
            working_dir = f"./rag_storage/company_{company_id}"
            storage_usage = 0

            if os.path.exists(working_dir):
                storage_usage = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(working_dir)
                    for filename in filenames
                )

            max_storage = 5 * 1024 * 1024 * 1024  # 5GB 限制
            storage_usage_percent = (storage_usage / max_storage) * 100

            return {
                "company_id": company_id,
                "documents": {
                    "current": doc_count,
                    "limit": max_documents,
                    "usage_percent": doc_usage_percent,
                    "available": max_documents - doc_count,
                },
                "storage": {
                    "current_bytes": storage_usage,
                    "current_mb": storage_usage / 1024 / 1024,
                    "limit_bytes": max_storage,
                    "limit_mb": max_storage / 1024 / 1024,
                    "usage_percent": storage_usage_percent,
                    "available_mb": (max_storage - storage_usage) / 1024 / 1024,
                },
                "warnings": self._get_quota_warnings(
                    doc_usage_percent, storage_usage_percent
                ),
            }

        except Exception as e:
            return {
                "company_id": company_id,
                "error": f"Failed to check quota: {str(e)}",
            }

    def _get_quota_warnings(self, doc_usage: float, storage_usage: float) -> List[str]:
        """取得配額警告"""
        warnings = []

        if doc_usage > 90:
            warnings.append("Document limit nearly reached (>90%)")
        elif doc_usage > 80:
            warnings.append("Document usage high (>80%)")

        if storage_usage > 90:
            warnings.append("Storage limit nearly reached (>90%)")
        elif storage_usage > 80:
            warnings.append("Storage usage high (>80%)")

        return warnings

    def get_tenant_stats(self) -> Dict[str, any]:
        """取得多租戶統計資訊（完整實作）"""
        try:
            memory_usage = self._get_memory_usage()

            return {
                "active_tenants": len(self.tenant_services),
                "tenant_list": list(self.tenant_services.keys()),
                "memory_usage": memory_usage,
                "system_info": {
                    "total_services": len(self.tenant_services),
                    "service_status": {
                        company_id: service.get_status()
                        for company_id, service in self.tenant_services.items()
                    },
                },
            }
        except Exception as e:
            return {"error": f"Failed to get tenant stats: {str(e)}"}

    def _get_memory_usage(self) -> Dict[str, float]:
        """取得記憶體使用情況"""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "rss_mb": memory_info.rss / 1024 / 1024,  # 實際記憶體使用
                "vms_mb": memory_info.vms / 1024 / 1024,  # 虛擬記憶體使用
                "percent": process.memory_percent(),
            }
        except ImportError:
            return {"rss_mb": 0, "vms_mb": 0, "percent": 0}

    async def cleanup_inactive_services(self, max_idle_time: int = 3600):
        """清理閒置的服務實例（完整實作）"""
        try:
            import time

            current_time = time.time()

            inactive_companies = []
            for company_id, service in self.tenant_services.items():
                # 檢查服務最後使用時間
                if hasattr(service, "last_used_time"):
                    if current_time - service.last_used_time > max_idle_time:
                        inactive_companies.append(company_id)
                elif not service.initialized:
                    # 未初始化的服務也視為閒置
                    inactive_companies.append(company_id)

            # 清理閒置服務
            cleanup_count = 0
            for company_id in inactive_companies:
                await self.cleanup_company_service(company_id)
                cleanup_count += 1
                print(f"Cleaned up inactive service for company {company_id}")

            return {
                "cleaned_up": cleanup_count,
                "remaining_active": len(self.tenant_services),
                "inactive_companies": inactive_companies,
            }

        except Exception as e:
            return {"error": f"Failed to cleanup inactive services: {str(e)}"}

    # ===== 資源管理方法 =====

    async def check_company_resources(self, company_id: int) -> Dict[str, Any]:
        """檢查公司資源使用情況"""
        try:
            memory_stats = await self.resource_manager.check_memory_usage(company_id)
            storage_stats = await self.resource_manager.check_storage_quota(company_id)

            # 合併結果
            combined_status = "ok"
            if memory_stats.get("status") in ["warning", "critical"]:
                combined_status = memory_stats["status"]
            if storage_stats.get("status") in ["warning", "critical"]:
                combined_status = storage_stats["status"]

            return {
                "company_id": company_id,
                "memory": memory_stats,
                "storage": storage_stats,
                "overall_status": combined_status,
                "timestamp": asyncio.get_event_loop().time(),
            }

        except Exception as e:
            print(f"❌ 檢查公司資源失敗: {e}")
            return {"status": "error", "message": str(e)}

    async def cleanup_company_resources(
        self, company_id: int, days_old: int = 30
    ) -> Dict[str, Any]:
        """清理公司資源"""
        try:
            cleanup_result = await self.resource_manager.cleanup_old_data(
                company_id, days_old
            )

            # 同時清理記憶體中的快取（如果需要的話）
            if company_id in self.tenant_services:
                # 這裡可以添加額外的清理邏輯
                pass

            return {
                "company_id": company_id,
                **cleanup_result,
                "timestamp": asyncio.get_event_loop().time(),
            }

        except Exception as e:
            print(f"❌ 清理公司資源失敗: {e}")
            return {"status": "error", "message": str(e)}

    async def get_resource_monitoring_stats(self) -> Dict[str, Any]:
        """獲取資源監控統計"""
        try:
            total_companies = len(self.tenant_services)
            active_pools = len(self.processing_pools)

            # 收集所有公司的資源統計
            company_resources = {}
            for company_id in list(self.tenant_services.keys()):
                try:
                    resources = await self.check_company_resources(company_id)
                    company_resources[str(company_id)] = resources
                except Exception as e:
                    company_resources[str(company_id)] = {"error": str(e)}

            return {
                "total_companies": total_companies,
                "active_processing_pools": active_pools,
                "company_resources": company_resources,
                "resource_manager": {
                    "max_memory_per_company_mb": self.resource_manager.max_memory_per_company
                    / 1024
                    / 1024,
                    "max_storage_per_company_gb": self.resource_manager.max_storage_per_company
                    / 1024
                    / 1024
                    / 1024,
                },
                "timestamp": asyncio.get_event_loop().time(),
            }

        except Exception as e:
            print(f"❌ 獲取資源監控統計失敗: {e}")
            return {"status": "error", "message": str(e)}

    async def monitor_processing_pool_health(self) -> Dict[str, Any]:
        """監控處理線程池健康狀態"""
        try:
            pool_stats = {}

            for company_id, pool in self.processing_pools.items():
                try:
                    # 獲取線程池狀態
                    active_threads = len([t for t in pool._threads if t.is_alive()])
                    pool_stats[str(company_id)] = {
                        "max_workers": pool._max_workers,
                        "active_threads": active_threads,
                        "pending_tasks": (
                            pool._work_queue.qsize()
                            if hasattr(pool._work_queue, "qsize")
                            else 0
                        ),
                        "status": (
                            "healthy"
                            if active_threads <= pool._max_workers
                            else "overloaded"
                        ),
                    }
                except Exception as e:
                    pool_stats[str(company_id)] = {"error": str(e)}

            return {
                "total_pools": len(self.processing_pools),
                "pool_stats": pool_stats,
                "timestamp": asyncio.get_event_loop().time(),
            }

        except Exception as e:
            print(f"❌ 監控處理線程池健康狀態失敗: {e}")
            return {"status": "error", "message": str(e)}


# 全域單例
_multitenant_rag_service = None


def get_multitenant_rag_service() -> MultiTenantRAGService:
    """取得多租戶 RAG 服務單例"""
    global _multitenant_rag_service
    if _multitenant_rag_service is None:
        _multitenant_rag_service = MultiTenantRAGService()
    return _multitenant_rag_service
