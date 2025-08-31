"""
文檔攝取服務 - 適配獨立文件夾架構
負責文檔的上傳和初始處理
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session
from app.models.document import DocumentMetadata
from app.models.audit import AuditLog
from app.services.rag_anything import RAGAnythingService

logger = logging.getLogger(__name__)


class IngestionService:
    """文檔攝取服務 - 使用新的獨立文件夾架構"""

    def __init__(self, db: Session):
        self.db = db
        self.rag_service = RAGAnythingService()

    async def process_document_upload(
        self,
        file_path: str,
        original_filename: str,
        company_id: int,
        created_by: str,
        mime_type: str = "text/plain",
    ) -> Dict[str, Any]:
        """處理文檔上傳 - 使用獨立文件夾架構"""
        try:
            logger.info(f"開始處理文檔上傳: {original_filename} (公司: {company_id})")

            # 創建文檔元數據記錄
            doc_metadata = DocumentMetadata(
                document_id="",  # 會在處理時生成
                original_filename=original_filename,
                file_path=file_path,
                file_size=Path(file_path).stat().st_size,
                mime_type=mime_type,
                company_id=company_id,
                created_by=created_by,
                processing_status="processing",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            self.db.add(doc_metadata)
            self.db.commit()
            self.db.refresh(doc_metadata)

            # 異步處理文檔
            processing_result = await self.rag_service.process_document(
                file_path=file_path, company_id=company_id
            )

            # 更新文檔元數據
            if processing_result["status"] == "success":
                doc_metadata.document_id = processing_result["doc_id"]
                doc_metadata.processing_status = "completed"
                doc_metadata.file_path = processing_result["storage_path"]
                doc_metadata.updated_at = datetime.now()

                # 創建審計日誌
                audit_log = AuditLog(
                    action="document_processed",
                    entity_type="document",
                    entity_id=processing_result["doc_id"],
                    user_id=created_by,
                    company_id=company_id,
                    details={
                        "original_filename": original_filename,
                        "chunks_count": processing_result["chunks_count"],
                        "processing_time": processing_result["processing_time"],
                    },
                    created_at=datetime.now(),
                )
                self.db.add(audit_log)

            else:
                doc_metadata.processing_status = "failed"
                doc_metadata.error_message = processing_result.get("error", "處理失敗")
                doc_metadata.updated_at = datetime.now()

                # 創建失敗審計日誌
                audit_log = AuditLog(
                    action="document_processing_failed",
                    entity_type="document",
                    entity_id=str(doc_metadata.id),
                    user_id=created_by,
                    company_id=company_id,
                    details={
                        "original_filename": original_filename,
                        "error": processing_result.get("error", "未知錯誤"),
                    },
                    created_at=datetime.now(),
                )
                self.db.add(audit_log)

            self.db.commit()

            return {
                "status": processing_result["status"],
                "document_id": processing_result.get("doc_id", ""),
                "message": processing_result.get("message", ""),
                "chunks_count": processing_result.get("chunks_count", 0),
                "processing_time": processing_result.get("processing_time", 0),
            }

        except Exception as e:
            logger.error(f"文檔上傳處理失敗: {e}")
            return {
                "status": "error",
                "message": f"文檔上傳處理失敗: {str(e)}",
            }

    async def delete_document(
        self, document_id: str, company_id: int, deleted_by: str
    ) -> Dict[str, Any]:
        """刪除文檔 - 使用獨立文件夾架構的原子刪除"""
        try:
            logger.info(f"開始刪除文檔: {document_id} (公司: {company_id})")

            # 從數據庫獲取文檔元數據
            doc_metadata = (
                self.db.query(DocumentMetadata)
                .filter(
                    DocumentMetadata.document_id == document_id,
                    DocumentMetadata.company_id == company_id,
                )
                .first()
            )

            if not doc_metadata:
                return {
                    "status": "error",
                    "message": f"文檔不存在: {document_id}",
                }

            # 調用 RAG 服務刪除文檔
            delete_result = await self.rag_service.delete_document(
                doc_id=document_id, company_id=str(company_id)
            )

            if delete_result["status"] == "success":
                # 從數據庫刪除元數據
                self.db.delete(doc_metadata)

                # 創建刪除審計日誌
                audit_log = AuditLog(
                    action="document_deleted",
                    entity_type="document",
                    entity_id=document_id,
                    user_id=deleted_by,
                    company_id=company_id,
                    details={
                        "original_filename": doc_metadata.original_filename,
                        "freed_space": delete_result.get("freed_space", 0),
                        "freed_space_mb": delete_result.get("freed_space_mb", 0),
                    },
                    created_at=datetime.now(),
                )
                self.db.add(audit_log)
                self.db.commit()

                return {
                    "status": "success",
                    "message": f"文檔 {document_id} 已成功刪除",
                    "freed_space": delete_result.get("freed_space", 0),
                    "freed_space_mb": delete_result.get("freed_space_mb", 0),
                }

            else:
                return {
                    "status": "error",
                    "message": delete_result.get("message", "刪除失敗"),
                }

        except Exception as e:
            logger.error(f"文檔刪除失敗: {e}")
            self.db.rollback()
            return {
                "status": "error",
                "message": f"文檔刪除失敗: {str(e)}",
            }


def get_ingestion_service(db: Session) -> IngestionService:
    """獲取攝取服務實例"""
    return IngestionService(db)
