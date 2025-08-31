"""
文檔生命週期管理器 - 簡化版本
統一管理文檔的上傳、處理、查詢、刪除全流程
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from sqlalchemy.orm import Session
from app.models.document import DocumentMetadata
from app.services.rag_anything import RAGAnythingService

logger = logging.getLogger(__name__)


class DocumentLifecycleManager:
    """文檔生命週期管理器 - 簡化版本"""

    def __init__(self):
        self.max_retry_count = 3
        self.processing_tasks = {}  # task_id -> Future (from ThreadPoolExecutor)
        self.task_status = {}  # task_id -> status info
        self.rag_service = RAGAnythingService()

    async def _process_document_async(
        self,
        task_id: str,
        file_path: str,
        company_id: int,
        user_id: str,
        original_filename: str,
        document_id: str,  # 新增參數
    ) -> Dict[str, Any]:
        """異步處理文檔 - 簡化版本"""
        from app.core.database import SessionLocal
        
        db = None
        try:
            logger.info(f"異步處理文檔: {original_filename} (任務ID: {task_id}, 文檔ID: {document_id})")

            # 記錄任務狀態
            self.task_status[task_id] = {
                "status": "starting",
                "message": "初始化處理任務...",
                "document_id": document_id,
                "progress": 0
            }

            # 獲取新的資料庫會話
            db = SessionLocal()
            
            # 更新狀態為處理中
            doc_metadata = (
                db.query(DocumentMetadata)
                .filter(DocumentMetadata.document_id == document_id)
                .first()
            )
            
            if doc_metadata:
                doc_metadata.processing_status = "processing"
                db.commit()

            # 更新任務狀態
            self.task_status[task_id] = {
                "status": "processing",
                "message": "正在處理文檔內容...",
                "document_id": document_id,
                "progress": 20
            }

            # 調用 RAG 服務處理文檔
            result = await self.rag_service.process_document(
                file_path=file_path, company_id=company_id
            )

            if result["status"] == "success":
                # 更新數據庫為完成狀態
                if doc_metadata:
                    doc_metadata.processing_status = "completed"
                    doc_metadata.file_path = result["storage_path"]  # 更新為處理後的路徑
                    doc_metadata.processed_at = datetime.now()
                    db.commit()

                # 更新任務狀態為完成
                self.task_status[task_id] = {
                    "status": "completed",
                    "message": "文檔處理完成",
                    "document_id": document_id,
                    "progress": 100,
                    "result": result
                }

                logger.info(f"文檔處理成功: {result['doc_id']}")
            else:
                # 處理失敗
                if doc_metadata:
                    doc_metadata.processing_status = "failed"
                    doc_metadata.error_message = result.get("message", "處理失敗")
                    db.commit()
                
                # 更新任務狀態為失敗
                self.task_status[task_id] = {
                    "status": "failed",
                    "message": f"處理失敗: {result.get('message', '未知錯誤')}",
                    "document_id": document_id,
                    "progress": 0,
                    "error": result.get("message")
                }
                
                logger.error(f"文檔處理失敗: {result.get('message', '未知錯誤')}")

            # 清理任務記錄
            if task_id in self.processing_tasks:
                del self.processing_tasks[task_id]

            return result

        except Exception as e:
            logger.error(f"異步文檔處理失敗: {e}")
            
            # 更新任務狀態為錯誤
            self.task_status[task_id] = {
                "status": "error",
                "message": f"處理異常: {str(e)}",
                "document_id": document_id,
                "progress": 0,
                "error": str(e)
            }
            
            if db:
                db.rollback()
                # 更新為失敗狀態
                try:
                    doc_metadata = (
                        db.query(DocumentMetadata)
                        .filter(DocumentMetadata.document_id == document_id)
                        .first()
                    )
                    if doc_metadata:
                        doc_metadata.processing_status = "failed"
                        doc_metadata.error_message = str(e)
                        db.commit()
                except Exception as db_error:
                    logger.error(f"更新失敗狀態時出錯: {db_error}")

            # 清理任務記錄
            if task_id in self.processing_tasks:
                del self.processing_tasks[task_id]

            return {
                "status": "error",
                "task_id": task_id,
                "message": f"文檔處理失敗: {str(e)}",
            }
            
        finally:
            if db:
                db.close()

    async def delete_document(
        self, doc_id: str, company_id: int, user_id: str, db: Session
    ) -> Dict[str, Any]:
        """刪除文檔 - 使用原子文件夾刪除架構"""
        try:
            logger.info(f"開始刪除文檔: {doc_id} (公司: {company_id})")

            # 1. 先更新數據庫狀態為刪除中
            doc_metadata = (
                db.query(DocumentMetadata)
                .filter(
                    DocumentMetadata.document_id == doc_id,
                    DocumentMetadata.company_id == company_id,
                )
                .first()
            )

            if not doc_metadata:
                return {
                    "status": "error",
                    "message": f"文檔不存在: {doc_id}",
                    "doc_id": doc_id,
                }

            doc_metadata.processing_status = "deleting"
            doc_metadata.updated_at = datetime.now()
            db.commit()

            # 2. 執行原子文件夾刪除
            delete_result = await self.rag_service.delete_document(
                doc_id=doc_id, company_id=str(company_id)
            )

            if delete_result["status"] == "success":
                # 3. 更新數據庫為已刪除
                doc_metadata.processing_status = "deleted"
                doc_metadata.deleted_at = datetime.now()
                db.commit()

                logger.info(f"文檔刪除成功: {doc_id} - 釋放: {delete_result.get('freed_space_mb', 0):.1f}MB")
                
                return {
                    "status": "success",
                    "message": f"文檔 {doc_id} 已成功刪除",
                    "doc_id": doc_id,
                    "freed_space_mb": delete_result.get("freed_space_mb", 0),
                }
            else:
                # 4. 刪除失敗，回滾狀態
                doc_metadata.processing_status = "failed"
                doc_metadata.error_message = delete_result.get("message", "刪除失敗")
                db.commit()
                
                return delete_result

        except Exception as e:
            logger.error(f"文檔刪除失敗: {e}")
            db.rollback()

            return {
                "status": "error",
                "message": f"文檔刪除失敗: {str(e)}",
                "doc_id": doc_id,
            }

    async def query_documents(
        self, query: str, company_id: int, limit: int = 10, **kwargs
    ) -> Dict[str, Any]:
        """查詢文檔"""
        try:
            logger.info(f"開始查詢文檔: {query[:50]}... (公司: {company_id})")

            # 調用 RAG 服務查詢
            result = await self.rag_service.query_documents(
                query=query, company_id=str(company_id), **kwargs
            )

            # 限制結果數量
            if "results" in result and len(result["results"]) > limit:
                result["results"] = result["results"][:limit]

            return result

        except Exception as e:
            logger.error(f"文檔查詢失敗: {e}")

            return {
                "status": "error",
                "message": f"查詢失敗: {str(e)}",
                "query": query,
            }

    def get_processing_status(self, task_id: str) -> Dict[str, Any]:
        """獲取處理狀態"""
        # 優先從任務狀態緩存中獲取
        if task_id in self.task_status:
            status_info = self.task_status[task_id].copy()
            status_info["task_id"] = task_id
            return status_info
        
        # 如果緩存中沒有，檢查任務是否存在（Future 對象）
        if task_id in self.processing_tasks:
            future = self.processing_tasks[task_id]
            if future.done():
                try:
                    result = future.result()
                    return {
                        "status": "completed" if result.get("status") == "success" else "failed",
                        "task_id": task_id,
                        "message": result.get("message", "處理完成"),
                        "progress": 100 if result.get("status") == "success" else 0
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "task_id": task_id,
                        "message": f"處理失敗: {str(e)}",
                        "progress": 0
                    }
            else:
                return {
                    "status": "processing",
                    "task_id": task_id,
                    "message": "文檔處理中...",
                    "progress": 50
                }
        else:
            return {
                "status": "not_found",
                "task_id": task_id,
                "message": "任務不存在",
                "progress": 0
            }

    async def cleanup_completed_tasks(self):
        """清理已完成的任務"""
        completed_tasks = [
            task_id for task_id, task in self.processing_tasks.items() if task.done()
        ]

        for task_id in completed_tasks:
            del self.processing_tasks[task_id]

        logger.info(f"清理了 {len(completed_tasks)} 個已完成的任務")

    # ========== 私有方法 ==========

    async def _execute_deletion_process(
        self, company_id: str, document_id: str
    ) -> bool:
        """執行實際的刪除流程 - 使用新的獨立文件夾架構原子刪除"""
        try:
            # 直接使用 RAGAnythingService 的原子刪除功能
            delete_result = await self.rag_service.delete_document(
                doc_id=document_id, company_id=company_id
            )

            success = delete_result.get("status") == "success"
            if success:
                logger.info(
                    f"RAG 文檔刪除成功 - 釋放空間: {delete_result.get('freed_space_mb', 0):.1f}MB"
                )
            else:
                logger.warning(
                    f"RAG 刪除失敗: {delete_result.get('message', '未知錯誤')}"
                )

            return success

        except Exception as e:
            logger.error(f"刪除流程執行失敗: {e}")
            return False


# 全域實例
_lifecycle_manager = None


def get_document_lifecycle_manager() -> DocumentLifecycleManager:
    """獲取文檔生命週期管理器實例"""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = DocumentLifecycleManager()
    return _lifecycle_manager