"""
文檔處理服務
支援 PDF/WORD 轉圖片並進行 OCR 文字識別
"""
import os
import tempfile
from typing import List, Tuple
from pathlib import Path
import logging

logger = logging.getLogger("linerag.services.docproc")
import fitz  # PyMuPDF
try:
    from docx2pdf import convert
    DOCX2PDF_AVAILABLE = True
except ImportError:
    logger.warning("docx2pdf not available - OCR for Word documents will be disabled")
    DOCX2PDF_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    logger.warning("PIL not available - image processing will be disabled")
    PIL_AVAILABLE = False

import uuid
class DocumentProcessor:
    def __init__(self):
        self.multimodal_service = None
        
    def pdf_to_images(self, pdf_path: str, output_dir: str) -> List[str]:
        """
        將 PDF 轉換為圖片
        
        Args:
            pdf_path: PDF 文件路徑
            output_dir: 輸出目錄
            
        Returns:
            圖片文件路徑列表
        """
        image_paths = []
        
        try:
            # 打開 PDF
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                # 獲取頁面
                page = pdf_document.load_page(page_num)
                
                # 設定渲染參數（提高解析度）
                mat = fitz.Matrix(2.0, 2.0)  # 2倍縮放
                pix = page.get_pixmap(matrix=mat)
                
                # 保存為圖片
                image_filename = f"page_{page_num + 1}.png"
                image_path = os.path.join(output_dir, image_filename)
                pix.save(image_path)
                image_paths.append(image_path)
                
            pdf_document.close()
            logger.info(f"PDF converted pages={len(image_paths)}")
            
        except Exception as e:
            logger.exception("PDF conversion failed")
            raise
            
        return image_paths
    
    def word_to_images(self, word_path: str, output_dir: str) -> List[str]:
        """
        將 Word 文檔轉換為圖片
        
        Args:
            word_path: Word 文件路徑
            output_dir: 輸出目錄
            
        Returns:
            圖片文件路徑列表
        """
        if not DOCX2PDF_AVAILABLE:
            raise ImportError("docx2pdf not available - cannot convert Word documents for OCR")
            
        try:
            # 先轉換為 PDF
            temp_pdf_path = os.path.join(output_dir, "temp.pdf")
            convert(word_path, temp_pdf_path)
            
            # 再將 PDF 轉為圖片
            image_paths = self.pdf_to_images(temp_pdf_path, output_dir)
            
            # 清理臨時 PDF
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
                
            logger.info(f"Word converted pages={len(image_paths)}")
            return image_paths
            
        except Exception as e:
            logger.exception("Word conversion failed")
            # 如果轉換失敗，嘗試直接使用原有的文字提取方法
            raise
    
    def _get_multimodal_service(self):
        """Lazy loading of multimodal service to avoid circular imports"""
        if self.multimodal_service is None:
            try:
                from app.services.multimodal_service import get_multimodal_service
                self.multimodal_service = get_multimodal_service()
            except ImportError as e:
                logger.exception("Import multimodal service failed")
                return None
        return self.multimodal_service
    
    def extract_text_from_images(self, image_paths: List[str]) -> List[Tuple[int, str]]:
        """
        從圖片列表中提取文字
        
        Args:
            image_paths: 圖片路徑列表
            
        Returns:
            (頁碼, 文字內容) 的列表
        """
        multimodal_service = self._get_multimodal_service()
        if multimodal_service is None:
            logger.error("Multimodal service unavailable; OCR disabled")
            return []
            
        extracted_texts = []
        
        for i, image_path in enumerate(image_paths):
            try:
                logger.info(f"OCR processing page={i + 1}")
                text = multimodal_service.extract_text_from_image(image_path)
                
                if text.strip():  # 只保存非空文字
                    extracted_texts.append((i + 1, text))
                    logger.info(f"OCR extracted page={i + 1}")
                else:
                    logger.warning(f"OCR empty page={i + 1}")
                    
            except Exception as e:
                logger.exception(f"OCR extract failed page={i + 1}")
                continue
                
        return extracted_texts
    
    def process_document_with_ocr(self, file_path: str, original_name: str) -> List[Tuple[int, str]]:
        """
        使用 OCR 處理文檔
        
        Args:
            file_path: 文件路徑
            original_name: 原始文件名
            
        Returns:
            (頁碼, 文字內容) 的列表
        """
        # 創建臨時目錄
        temp_dir = tempfile.mkdtemp(prefix=f"doc_ocr_{uuid.uuid4().hex[:8]}_")
        
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # 根據文件類型轉換為圖片
            if file_extension == '.pdf':
                image_paths = self.pdf_to_images(file_path, temp_dir)
            elif file_extension in ['.doc', '.docx']:
                image_paths = self.word_to_images(file_path, temp_dir)
            else:
                raise ValueError(f"不支援的文件格式: {file_extension}")
            
            # 從圖片中提取文字
            extracted_texts = self.extract_text_from_images(image_paths)
            
            logger.info(f"OCR done file={original_name} pages={len(extracted_texts)}")
            return extracted_texts
            
        finally:
            # 清理臨時文件
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Cleanup temp dir failed: {e}")

# 全局文檔處理器實例
document_processor = DocumentProcessor()

def get_document_processor() -> DocumentProcessor:
    """獲取文檔處理器實例"""
    return document_processor