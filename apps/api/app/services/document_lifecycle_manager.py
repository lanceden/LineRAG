"""
文檔生命週期管理器
統一管理文檔的上傳、處理、查詢、刪除全流程
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import uuid

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.document import DocumentMetadata
from app.utils.namespace import AsyncNamespaceContext

logger = logging.getLogger(__name__)


class DocumentStatus(str, Enum):
    """文檔狀態枚舉"""
    UPLOADED = "uploaded"        # 已上傳，等待處理
    PROCESSING = "processing"    # 處理中
    COMPLETED = "completed"      # 處理完成
    FAILED = "failed"           # 處理失敗
    DELETING = "deleting"       # 刪除中
    DELETED = "deleted"         # 已刪除


class ProcessingStage(str, Enum):
    """處理階段枚舉"""
    UPLOAD = "upload"           # 文件上傳
    VALIDATE = "validate"       # 文件驗證
    PARSE = "parse"            # 文檔解析
    EMBED = "embed"            # 向量嵌入
    INDEX = "index"            # 索引構建
    GRAPH = "graph"            # 知識圖譜
    COMPLETE = "complete"      # 處理完成


class DocumentLifecycleManager:
    """文檔生命週期管理器"""
    
    def __init__(self):
        self.max_retry_count = 3
        self.processing_tasks = {}  # task_id -> asyncio.Task
        
    async def upload_document(
        self, 
        company_id: int,
        file_path: str, 
        original_filename: str,
        uploaded_by: str = None
    ) -> Dict[str, Any]:
        """
        文檔上傳入口
        
        Returns:
            {
                "status": "success",
                "document_id": "xxx",
                "task_id": "xxx"
            }
        """
        try:
            # 1. 生成唯一標識
            document_id = str(uuid.uuid4())
            task_id = str(uuid.uuid4())
            
            logger.info(f"開始文檔上傳流程 - 公司:{company_id}, 文檔:{document_id}")
            
            # 2. 創建數據庫記錄
            db_record = await self._create_document_record(
                company_id=company_id,
                document_id=document_id,
                file_path=file_path,
                original_filename=original_filename,
                uploaded_by=uploaded_by
            )
            
            # 3. 異步啟動處理任務
            processing_task = asyncio.create_task(
                self._process_document_async(document_id, task_id)
            )
            self.processing_tasks[task_id] = processing_task
            
            # 4. 立即返回
            return {
                "status": "success", 
                "document_id": document_id,
                "task_id": task_id,
                "message": "文檔上傳成功，處理已在背景啟動"
            }
            
        except Exception as e:
            logger.error(f"文檔上傳失敗: {e}")
            return {
                "status": "error",
                "message": f"文檔上傳失敗: {str(e)}"
            }
    
    async def delete_document(
        self,
        company_id: int, 
        document_id: str
    ) -> Dict[str, Any]:
        """
        文檔刪除入口
        
        Returns:
            {
                "status": "success",
                "message": "文檔刪除成功"
            }
        """
        try:
            logger.info(f"開始文檔刪除流程 - 公司:{company_id}, 文檔:{document_id}")
            
            # 1. 更新狀態為刪除中
            await self._update_document_status(
                document_id, 
                DocumentStatus.DELETING,
                stage=ProcessingStage.COMPLETE.value
            )
            
            # 2. 執行完整刪除流程
            async with AsyncNamespaceContext(company_id):
                success = await self._execute_deletion_process(company_id, document_id)
                
                if success:
                    # 3. 標記為已刪除
                    await self._update_document_status(
                        document_id,
                        DocumentStatus.DELETED
                    )
                    
                    return {
                        "status": "success",
                        "message": "文檔刪除成功"
                    }
                else:
                    return {
                        "status": "error", 
                        "message": "文檔刪除過程中出現錯誤"
                    }
                    
        except Exception as e:
            logger.error(f"文檔刪除失敗: {e}")
            return {
                "status": "error",
                "message": f"文檔刪除失敗: {str(e)}"
            }
    
    async def get_document_status(
        self, 
        document_id: str
    ) -> Dict[str, Any]:
        """獲取文檔處理狀態"""
        try:
            db = next(get_db())
            try:
                doc = db.query(DocumentMetadata).filter(
                    DocumentMetadata.document_id == document_id
                ).first()
                
                if not doc:
                    return {
                        "status": "error",
                        "message": "文檔不存在"
                    }
                
                return {
                    "status": "success",
                    "document_id": document_id,
                    "processing_status": doc.processing_status,
                    "processing_stage": getattr(doc, 'processing_stage', None),
                    "progress_percent": getattr(doc, 'progress_percent', 0),
                    "error_message": doc.error_message,
                    "uploaded_at": doc.uploaded_at,
                    "processed_at": doc.processed_at
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"獲取文檔狀態失敗: {e}")
            return {
                "status": "error",
                "message": f"獲取文檔狀態失敗: {str(e)}"
            }
    
    # ========== 私有方法 ==========
    
    async def _create_document_record(
        self, 
        company_id: int,
        document_id: str,
        file_path: str, 
        original_filename: str,
        uploaded_by: str = None
    ) -> DocumentMetadata:
        """創建文檔數據庫記錄"""
        db = next(get_db())
        try:
            # 獲取文件信息
            file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
            
            doc = DocumentMetadata(
                company_id=company_id,
                document_id=document_id,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                processing_status=DocumentStatus.UPLOADED.value,
                uploaded_at=datetime.utcnow(),
                created_by=uploaded_by
            )
            
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            logger.info(f"文檔記錄已創建 - ID:{document_id}")
            return doc
            
        finally:
            db.close()
    
    async def _update_document_status(
        self,
        document_id: str,
        status: DocumentStatus,
        stage: str = None,
        progress: int = None,
        error_message: str = None
    ):
        """更新文檔狀態"""
        db = next(get_db())
        try:
            doc = db.query(DocumentMetadata).filter(
                DocumentMetadata.document_id == document_id
            ).first()
            
            if doc:
                doc.processing_status = status.value
                
                if stage:
                    # 需要先在數據庫模型中添加這些字段
                    if hasattr(doc, 'processing_stage'):
                        doc.processing_stage = stage
                        
                if progress is not None:
                    if hasattr(doc, 'progress_percent'):
                        doc.progress_percent = progress
                        
                if error_message:
                    doc.error_message = error_message
                    
                if status == DocumentStatus.COMPLETED:
                    doc.processed_at = datetime.utcnow()
                    
                db.commit()
                logger.info(f"文檔狀態已更新 - ID:{document_id}, 狀態:{status.value}")
                
        finally:
            db.close()
    
    async def _process_document_async(self, document_id: str, task_id: str):
        """異步處理文檔"""
        try:
            logger.info(f"開始處理文檔 - ID:{document_id}, 任務:{task_id}")
            
            # 獲取文檔信息
            db = next(get_db())
            try:
                doc = db.query(DocumentMetadata).filter(
                    DocumentMetadata.document_id == document_id
                ).first()
                
                if not doc:
                    logger.error(f"文檔不存在: {document_id}")
                    return
                    
                company_id = doc.company_id
                file_path = doc.file_path
                
            finally:
                db.close()
            
            # 更新狀態為處理中
            await self._update_document_status(
                document_id, 
                DocumentStatus.PROCESSING,
                stage=ProcessingStage.PARSE.value,
                progress=10
            )
            
            # 調用實際的處理邏輯
            async with AsyncNamespaceContext(company_id):
                success = await self._execute_processing_steps(
                    company_id, document_id, file_path
                )
                
                if success:
                    await self._update_document_status(
                        document_id,
                        DocumentStatus.COMPLETED, 
                        stage=ProcessingStage.COMPLETE.value,
                        progress=100
                    )
                    logger.info(f"文檔處理完成 - ID:{document_id}")
                else:
                    await self._update_document_status(
                        document_id,
                        DocumentStatus.FAILED,
                        error_message="處理過程中發生錯誤"
                    )
                    logger.error(f"文檔處理失敗 - ID:{document_id}")
            
        except Exception as e:
            logger.error(f"文檔處理異常 - ID:{document_id}, 錯誤:{e}")
            await self._update_document_status(
                document_id,
                DocumentStatus.FAILED,
                error_message=str(e)
            )
        finally:
            # 清理任務引用
            if task_id in self.processing_tasks:
                del self.processing_tasks[task_id]
    
    async def _execute_processing_steps(
        self, 
        company_id: int, 
        document_id: str, 
        file_path: str
    ) -> bool:
        """執行實際的處理步驟"""
        try:
            # 這裡調用現有的 RAG-Anything 處理邏輯
            from app.services.rag_anything import get_rag_service
            
            rag_service = get_rag_service()
            await rag_service.initialize(str(company_id))
            
            # 處理文檔
            result = await rag_service.process_document(
                file_path, str(company_id)
            )
            
            return result.get("status") == "success"
            
        except Exception as e:
            logger.error(f"處理步驟執行失敗: {e}")
            return False
    
    async def _execute_deletion_process(
        self,
        company_id: int, 
        document_id: str
    ) -> bool:
        """執行實際的刪除流程"""
        try:
            # 調用現有的刪除邏輯
            from app.services.rag_anything import get_rag_service
            
            rag_service = get_rag_service()
            await rag_service.initialize(str(company_id))
            
            result = await rag_service.delete_document(document_id, str(company_id))
            
            return result.get("status") == "success"
            
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