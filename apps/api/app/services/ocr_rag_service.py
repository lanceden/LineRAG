"""
OCR RAG 服務
提供穩定的文檔處理和查詢功能
支援：PDF, Word, 圖片, 純文字, Excel
"""

import os
import uuid
from typing import List, Dict, Any
import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from PIL import Image
import pytesseract
from docx import Document
import PyPDF2
from pdf2image import convert_from_path
import openai
from pathlib import Path


class OCRRAGService:
    """OCR RAG 服務類"""
    
    def __init__(self, openai_api_key: str, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.initialized = False
        
    async def initialize(self, collection_name: str = "ocr_documents"):
        """初始化服務"""
        try:
            self.collection_name = collection_name
            
            # 檢查並創建 collection
            try:
                collections = self.qdrant_client.get_collections()
                collection_names = [col.name for col in collections.collections]
                
                if self.collection_name not in collection_names:
                    self.qdrant_client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=384,  # all-MiniLM-L6-v2 的向量維度
                            distance=Distance.COSINE
                        )
                    )
                    print(f"已創建 Qdrant collection: {self.collection_name}")
                else:
                    print(f"使用現有 Qdrant collection: {self.collection_name}")
            except Exception as e:
                print(f"Qdrant collection 初始化錯誤: {e}")
                # 如果是409衝突錯誤，繼續執行（collection已存在）
                if "409" in str(e) or "already exists" in str(e).lower():
                    print(f"Collection {self.collection_name} 已存在，繼續使用")
                else:
                    raise
                
            self.initialized = True
            print("OCR RAG 服務初始化成功")
            
        except Exception as e:
            print(f"OCR RAG 服務初始化失敗: {e}")
            raise
    
    def extract_text(self, file_path: str) -> str:
        """統一文本提取"""
        print(f"處理文件: {file_path}")
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.jpg', '.jpeg', '.png']:
            print("  → 圖片 OCR")
            return self._ocr_image(file_path)
            
        elif ext == '.pdf':
            print("  → PDF 轉圖片 OCR")
            return self._ocr_pdf(file_path)
            
        elif ext == '.docx':
            print("  → Word 文檔處理")
            return self._process_word(file_path)
            
        elif ext in ['.xlsx', '.xls']:
            print("  → Excel 表格讀取")
            return self._read_excel(file_path)
            
        elif ext == '.txt':
            print("  → 純文字讀取")
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"不支援的文件格式: {ext}")
    
    def _ocr_image(self, image_path: str) -> str:
        """圖片 OCR"""
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='chi_tra+eng')
        return text
    
    def _ocr_pdf(self, pdf_path: str) -> str:
        """PDF 轉圖片 OCR"""
        try:
            images = convert_from_path(pdf_path)
            all_text = []
            
            for i, image in enumerate(images):
                print(f"    處理第 {i+1} 頁...")
                page_text = pytesseract.image_to_string(image, lang='chi_tra+eng')
                all_text.append(f"=== 第 {i+1} 頁 ===\n{page_text}")
            
            return "\n\n".join(all_text)
            
        except Exception as e:
            print(f"    PDF OCR 失敗，嘗試文字提取: {e}")
            # 備用方案：直接提取文字
            try:
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                return text
            except Exception as e2:
                print(f"    文字提取也失敗: {e2}")
                return ""
    
    def _process_word(self, docx_path: str) -> str:
        """Word 文檔處理"""
        try:
            doc = Document(docx_path)
            direct_text = '\n'.join([para.text for para in doc.paragraphs])
            
            if len(direct_text.strip()) > 50:
                print("    直接提取 Word 文字成功")
                return direct_text
        except Exception as e:
            print(f"    Word 文字提取失敗: {e}")
        
        print("    Word 文檔建議先轉成 PDF 再處理")
        return ""
    
    def _read_excel(self, excel_path: str) -> str:
        """Excel 表格讀取"""
        try:
            # 讀取所有工作表
            df_dict = pd.read_excel(excel_path, sheet_name=None)
            
            text_content = []
            for sheet_name, df in df_dict.items():
                text_content.append(f"=== 工作表: {sheet_name} ===")
                
                # 轉成可讀的文字格式
                df_str = df.to_string(index=False, na_rep='')
                text_content.append(df_str)
                
                # 也加入基本統計
                if not df.empty:
                    text_content.append(f"行數: {len(df)}, 列數: {len(df.columns)}")
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            print(f"    Excel 讀取失敗: {e}")
            return ""
    
    def _extract_document_metadata(self, text: str, file_path: str) -> Dict[str, Any]:
        """提取文檔級別的 metadata"""
        try:
            # 基本統計
            word_count = len(text.split())
            char_count = len(text)
            
            # 嘗試提取結構化資訊
            metadata = {
                "word_count": word_count,
                "char_count": char_count,
                "document_type": self._detect_document_type(text),
                "key_topics": self._extract_key_topics(text),
                "document_summary": self._generate_summary(text)
            }
            
            return metadata
        except Exception as e:
            print(f"提取 metadata 失敗: {e}")
            return {"word_count": 0, "char_count": 0}
    
    def _detect_document_type(self, text: str) -> str:
        """檢測文檔類型"""
        text_lower = text.lower()
        if any(word in text_lower for word in ["案例", "成功", "客戶"]):
            return "case_study"
        elif any(word in text_lower for word in ["功能", "系統", "管理"]):
            return "product_info"
        elif any(word in text_lower for word in ["價格", "費用", "收費"]):
            return "pricing"
        elif any(word in text_lower for word in ["公司", "關於", "介紹"]):
            return "company_info"
        else:
            return "general"
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """提取關鍵主題"""
        keywords = ["運動", "健身", "預約", "管理", "系統", "會員", "課程", "場館", "收費", "功能"]
        found_topics = [kw for kw in keywords if kw in text]
        return found_topics[:5]  # 最多5個主題
    
    def _generate_summary(self, text: str) -> str:
        """生成文檔摘要"""
        # 簡單摘要：取前200字符
        return text[:200].strip() + "..." if len(text) > 200 else text.strip()
    
    def split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """文本分塊"""
        if not text or len(text.strip()) < 10:
            return []
            
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk.strip()) > 10:  # 忽略太短的塊
                chunks.append(chunk)
                
        return chunks
    
    async def add_document(self, file_path: str, company_id: str = None) -> bool:
        """添加文檔到向量庫"""
        if not self.initialized:
            raise RuntimeError("服務未初始化")
            
        try:
            # 提取文本
            text = self.extract_text(file_path)
            
            if not text or len(text.strip()) < 10:
                print(f"    警告: 文件內容為空或太短")
                return False
                
            print(f"    提取文本長度: {len(text)} 字符")
            
            # 分塊
            chunks = self.split_text(text)
            if not chunks:
                print(f"    警告: 分塊後無內容")
                return False
                
            print(f"    分成 {len(chunks)} 個塊")
            
            # 生成嵌入
            print("    生成向量嵌入...")
            embeddings = self.embedder.encode(chunks)
            
            # 提取文檔 metadata
            doc_metadata = self._extract_document_metadata(text, file_path)
            
            # 存儲到 Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # 為每個 chunk 添加豐富的 metadata
                chunk_metadata = {
                    "text": chunk,
                    "source": file_path,
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "filename": os.path.basename(file_path),
                    "company_id": company_id or "default",
                    "file_type": Path(file_path).suffix.lower(),
                    "chunk_position": "start" if i == 0 else "end" if i == len(chunks)-1 else "middle",
                    "prev_chunk_preview": chunks[i-1][:100] + "..." if i > 0 else "",
                    "next_chunk_preview": chunks[i+1][:100] + "..." if i < len(chunks)-1 else "",
                    **doc_metadata  # 添加文檔級別的 metadata
                }
                
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload=chunk_metadata
                )
                points.append(point)
            
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            print(f"    成功添加 {len(chunks)} 個文本塊到 Qdrant")
            return True
            
        except Exception as e:
            print(f"    添加文檔失敗: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    async def query(self, question: str, company_id: str = None, top_k: int = 3) -> str:
        """查詢"""
        if not self.initialized:
            raise RuntimeError("服務未初始化")
            
        print(f"\n查詢: {question}")
        
        try:
            # 生成查詢向量
            query_embedding = self.embedder.encode([question])
            
            # 構建過濾條件（如果有company_id）
            query_filter = None
            if company_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="company_id",
                            match=MatchValue(value=company_id)
                        )
                    ]
                )
            
            # 檢索相關文檔
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding[0].tolist(),  # 取第一個向量並轉為列表
                limit=top_k,
                query_filter=query_filter
            )
            
            if not search_result:
                return "抱歉，找不到相關資料。"
            
            # 組裝上下文，利用 metadata 提供更豐富的資訊
            context_parts = []
            for result in search_result:
                payload = result.payload
                source = payload.get("filename", "unknown")
                text = payload.get("text", "")
                score = result.score
                
                # 添加上下文資訊
                chunk_position = payload.get("chunk_position", "")
                prev_preview = payload.get("prev_chunk_preview", "")
                next_preview = payload.get("next_chunk_preview", "")
                doc_type = payload.get("document_type", "")
                
                # 構建豐富的上下文
                context_info = f"[來源: {source}]"
                if doc_type:
                    context_info += f" [類型: {doc_type}]"
                if chunk_position:
                    context_info += f" [位置: {chunk_position}]"
                context_info += f" (相似度: {score:.3f})"
                
                full_context = context_info + "\n" + text
                
                # 如果有前後文預覽，添加到上下文中
                if prev_preview and chunk_position != "start":
                    full_context += f"\n[前文: {prev_preview}]"
                if next_preview and chunk_position != "end":
                    full_context += f"\n[後文: {next_preview}]"
                
                context_parts.append(full_context)
            
            context = "\n\n".join(context_parts)
            print(f"找到 {len(context_parts)} 個相關片段")
            
            # 用 GPT 生成答案
            prompt = f"""你是一個親切專業的客服人員，請根據以下資料回答用戶問題。

參考資料：
{context}

用戶問題：{question}

回答要求：
- 保持親切友善的客服語氣
- 提供清楚詳細的資訊
- 可以適度表達關心，但不要每次都用相同的結尾句
- 偶爾可以問「還有其他問題嗎？」但不要制式化
- 語氣要像真人客服，自然變化不要太機械"""

            # 使用 context7 方式：提供 7 個優質回覆範例作為學習參考
            context7_examples = """
以下是優質客服回覆範例，請學習這種語調和結尾方式的變化：

範例1：
問：系統多少錢？
答：我們的系統採用模組化計價，依據您選擇的功能來報價。建議您先告訴我場館類型和需求，我可以提供更精確的報價。

範例2：
問：安裝需要多久？
答：一般來說需要1-2週工作天，主要看場館規模和資料準備情況。我們會有專人協助您完成設定。

範例3：
問：有沒有教學？
答：有的，我們提供完整的線上教學和操作手冊，確保您的團隊能快速上手。

範例4：
問：系統穩定嗎？
答：我們已經服務超過60家場館，系統運行非常穩定，還有完善的備份機制保障資料安全。

範例5：
問：能客製化嗎？
答：當然可以！我們專為運動產業設計，能根據您的場館特性進行功能調整。

範例6：
問：支援哪些支付方式？
答：支援信用卡、行動支付、現金等多種方式，讓會員付款更便利。

範例7：
問：有demo可以看嗎？
答：有的，我可以安排線上展示，讓您實際體驗系統功能。方便的話可以約個時間？
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"""你是運動場館管理系統的專業客服。

{context7_examples}

請參考以上範例的語調和風格來回答用戶問題：
- 語氣自然親切，但不過度客套
- 直接回答重點，簡潔有力
- 仔細理解用戶問題的真正意思，特別注意上下文語境
- 如果用戶問題不完整或有歧義，先嘗試理解最合理的意思再回答
- 結尾要有變化：有時直接結束，有時簡單關心，有時反問需求
- 絕對避免重複使用相同的結尾句式
- 語調要像真人客服，不要太機械化"""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"查詢失敗: {e}")
            return f"查詢出現錯誤: {e}"
    
    async def delete_document(self, file_path: str, company_id: str = None) -> bool:
        """從向量庫中刪除文檔"""
        if not self.initialized:
            raise RuntimeError("服務未初始化")
            
        try:
            print(f"刪除文檔: {file_path}")
            
            # 構建過濾條件
            filename = os.path.basename(file_path)
            
            # 創建過濾條件列表
            conditions = [
                FieldCondition(
                    key="filename",
                    match=MatchValue(value=filename)
                )
            ]
            
            # 如果指定了 company_id，添加到過濾條件
            if company_id:
                conditions.append(
                    FieldCondition(
                        key="company_id",
                        match=MatchValue(value=company_id)
                    )
                )
            
            # 創建過濾器
            delete_filter = Filter(must=conditions)
            
            # 使用 delete 方法刪除匹配的向量點
            result = self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=delete_filter
            )
            
            print(f"刪除文檔成功: {filename}")
            return True
            
        except Exception as e:
            print(f"刪除文檔失敗: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    async def query_text(self, question: str, mode: str = "hybrid", top_k: int = 3) -> str:
        """文本查詢（兼容多租戶接口）"""
        # 使用現有的 query 方法，mode 參數暫時忽略
        return await self.query(question, top_k=top_k)
    
    def get_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        return {
            "initialized": self.initialized,
            "collection_name": getattr(self, 'collection_name', None),
            "last_used_time": getattr(self, 'last_used_time', None)
        }
    
    async def process_document(self, file_path: str, company_id: str = None, output_dir: str = None) -> Dict[str, Any]:
        """處理文檔（兼容多租戶接口）"""
        try:
            print(f"處理文檔: {file_path} (公司ID: {company_id})")
            
            # 更新最後使用時間
            import time
            self.last_used_time = time.time()
            
            # 添加文檔到向量庫
            success = await self.add_document(file_path, company_id)
            
            if success:
                return {
                    "status": "success",
                    "message": "文檔處理成功",
                    "file_path": file_path,
                    "company_id": company_id,
                    "processed_chunks": "已添加到向量庫"
                }
            else:
                return {
                    "status": "failed",
                    "message": "文檔處理失敗",
                    "file_path": file_path,
                    "company_id": company_id,
                    "error": "無法提取文本或添加到向量庫"
                }
                
        except Exception as e:
            print(f"處理文檔失敗: {e}")
            import traceback
            print(traceback.format_exc())
            return {
                "status": "failed", 
                "message": f"文檔處理錯誤: {str(e)}",
                "file_path": file_path,
                "company_id": company_id,
                "error": str(e)
            }
    
    async def create_knowledge_graph_from_document(self, file_path: str, company_id: str = None) -> Dict[str, Any]:
        """從文檔創建知識圖譜（佔位方法，OCR RAG 暫不支持）"""
        print(f"知識圖譜創建請求: {file_path} (OCR RAG 暫不支持知識圖譜)")
        return {
            "status": "skipped",
            "message": "OCR RAG 架構暫不支持知識圖譜創建",
            "file_path": file_path,
            "company_id": company_id
        }


# 全局服務實例
_ocr_rag_service = None

def get_ocr_rag_service() -> OCRRAGService:
    """獲取 OCR RAG 服務實例"""
    global _ocr_rag_service
    if _ocr_rag_service is None:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        
        _ocr_rag_service = OCRRAGService(
            openai_api_key=openai_api_key,
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port
        )
    return _ocr_rag_service