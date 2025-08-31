"""
文檔元資料模型
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    BigInteger,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class DocumentMetadata(Base):
    """文檔元資料模型"""

    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(
        Integer, ForeignKey("companies.id"), nullable=False, comment="所屬公司ID"
    )

    # 文檔基本資訊
    document_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="RAG系統中的文檔ID",
    )
    lightrag_doc_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="LightRAG 內部文檔 ID (用於精確刪除)",
    )
    original_filename = Column(String(500), nullable=False, comment="原始檔名")
    file_path = Column(Text, comment="檔案路徑")
    file_size = Column(BigInteger, comment="檔案大小(bytes)")
    mime_type = Column(String(100), comment="檔案類型")

    # 處理資訊
    processing_method = Column(String(50), comment="處理方法: auto, ocr, traditional")
    processing_status = Column(
        String(50),
        default="pending",
        comment="處理狀態: pending, processing, completed, failed",
    )
    chunk_count = Column(Integer, default=0, comment="分塊數量")
    processing_time = Column(Integer, comment="處理時間(秒)")
    error_message = Column(Text, comment="錯誤訊息")

    # 進階處理狀態 (方案A 擴充)
    multimodal_processed = Column(Boolean, default=False, comment="多模態是否完成")
    content_hash = Column(String(64), index=True, comment="內容雜湊(去重用)")
    raw_status_json = Column(Text, comment="上游 LightRAG/RAGAnything 原始狀態 JSON")

    # 內容統計
    total_pages = Column(Integer, comment="總頁數")
    extracted_text_length = Column(Integer, comment="提取文字長度")
    has_images = Column(Boolean, default=False, comment="是否包含圖片")
    has_tables = Column(Boolean, default=False, comment="是否包含表格")
    has_formulas = Column(Boolean, default=False, comment="是否包含公式")

    # 存取統計
    access_count = Column(Integer, default=0, comment="存取次數")
    last_accessed = Column(DateTime, comment="最後存取時間")

    # 時間戳記
    uploaded_at = Column(DateTime, default=datetime.utcnow, comment="上傳時間")
    processed_at = Column(DateTime, comment="處理完成時間")
    deleted_at = Column(DateTime, comment="刪除時間")
    created_by = Column(String(255), comment="建立者")

    # 關聯
    company = relationship("Company", back_populates="documents")

    def __repr__(self):
        return f"<DocumentMetadata(id={self.id}, filename='{self.original_filename}', company_id={self.company_id})>"
