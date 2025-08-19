"""
多租戶 RAG-Anything 服務管理器
"""

import os
from typing import Dict, List, Optional
from pathlib import Path
from app.services.rag_anything import RAGAnythingService
from app.models.company import Company
from sqlalchemy.orm import Session


class MultiTenantRAGService:
    """多租戶 RAG 服務管理器"""

    def __init__(self):
        self.tenant_services: Dict[int, RAGAnythingService] = {}

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
        rag_service = RAGAnythingService()

        # 設定公司專用的工作目錄
        if company.rag_working_dir:
            working_dir = company.rag_working_dir
        else:
            working_dir = f"./rag_storage/company_{company_id}"
            # 更新資料庫記錄
            company.rag_working_dir = working_dir
            db.commit()

        # 確保目錄存在
        Path(working_dir).mkdir(parents=True, exist_ok=True)

        # 使用公司特定的環境變數（如果有的話）
        os.environ["RAG_WORKING_DIR"] = working_dir

        # 初始化服務
        await rag_service.initialize()

        # 快取服務實例
        self.tenant_services[company_id] = rag_service

        return rag_service

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


# 全域單例
_multitenant_rag_service = None


def get_multitenant_rag_service() -> MultiTenantRAGService:
    """取得多租戶 RAG 服務單例"""
    global _multitenant_rag_service
    if _multitenant_rag_service is None:
        _multitenant_rag_service = MultiTenantRAGService()
    return _multitenant_rag_service
