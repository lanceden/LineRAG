"""
多租戶 RAG-Anything 服務管理器
"""

import os
from typing import Dict, Optional
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


# 全域單例
_multitenant_rag_service = None


def get_multitenant_rag_service() -> MultiTenantRAGService:
    """取得多租戶 RAG 服務單例"""
    global _multitenant_rag_service
    if _multitenant_rag_service is None:
        _multitenant_rag_service = MultiTenantRAGService()
    return _multitenant_rag_service
