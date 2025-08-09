from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.document_loaders import (
    PyMuPDFLoader,
    Docx2txtLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)
from typing import Dict, List, Literal, Optional
import openai
import httpx
import uuid
import time
import os
import json
import tempfile
import shutil

# Import multimodal services with error handling
try:
    from multimodal_service import get_multimodal_service

    multimodal_available = True
except ImportError as e:
    print(f"Warning: Multimodal service not available: {e}")
    multimodal_available = False

try:
    from document_processor import get_document_processor

    document_processor_available = True
except ImportError as e:
    print(f"Warning: Document processor not available: {e}")
    document_processor_available = False

# 設定本地 vLLM API
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "not-needed"


class MessagePart(BaseModel):
    type: Literal["text", "image"]
    text: Optional[str] = None
    image_url: Optional[str] = None


class Message(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    parts: List[Dict[str, str]]


class AskRequest(BaseModel):
    messages: List[Message]
    trigger: Optional[str] = None


class IngestRequest(BaseModel):
    file_path: str
    original_name: str
    use_ocr: Optional[bool] = False  # 新增：是否使用 OCR 模式


class ImageQuestionRequest(BaseModel):
    image_path: str
    question: str


app = FastAPI(
    title="LineRAG API", description="RAG API with multimodal support", version="1.0.0"
)


@app.get("/")
def read_root():
    return {"message": "LineRAG API is running", "status": "ok"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "multimodal_available": multimodal_available,
        "document_processor_available": document_processor_available,
        "vectordb_available": vectordb is not None,
    }


# Qdrant 配置 (與 ingest.py 保持一致)
COLLECTION_NAME = "documents"
USE_LOCAL_MODE = True  # 與 ingest.py 保持一致

# Initialize embeddings with error handling
try:
    embedding = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3", encode_kwargs={"normalize_embeddings": True}
    )
    print("✅ 嵌入模型初始化成功")
except Exception as e:
    print(f"❌ 嵌入模型初始化失敗: {e}")
    embedding = None

# 初始化多模態服務 (with error handling)
multimodal_service = None
document_processor = None

if multimodal_available:
    try:
        multimodal_service = get_multimodal_service()
        print("✅ 多模態服務初始化成功")
    except Exception as e:
        print(f"❌ 多模態服務初始化失敗: {e}")

if document_processor_available:
    try:
        document_processor = get_document_processor()
        print("✅ 文檔處理器初始化成功")
    except Exception as e:
        print(f"❌ 文檔處理器初始化失敗: {e}")

# 初始化 Qdrant 客戶端和向量庫
vectordb = None
retriever = None

if embedding is not None:
    try:
        if USE_LOCAL_MODE:
            qdrant_client = QdrantClient(path="./local_qdrant")
            print("API 服務使用本地文件模式")
        else:
            qdrant_client = QdrantClient(host="localhost", port=6333)
            print("API 服務使用服務器模式")

        vectordb = Qdrant(
            client=qdrant_client, collection_name=COLLECTION_NAME, embeddings=embedding
        )
        retriever = vectordb.as_retriever()
        print("✅ 成功連接到 Qdrant 向量庫")

    except Exception as e:
        print(f"❌ Qdrant 初始化失敗: {e}")
        print("請確保:")
        if USE_LOCAL_MODE:
            print("- 本地 Qdrant 數據存在 (先運行 ingest.py 添加文檔)")
        else:
            print("- Qdrant 服務正在運行")
            print("- 集合 'documents' 已創建")
        vectordb = None
        retriever = None
else:
    print("❌ 無法初始化 Qdrant：嵌入模型不可用")


def build_prompt(messages: List[Message], max_rounds: int = 3) -> str:
    selected = messages[-max_rounds * 2 :]
    prompt = ""
    for msg in selected:
        role = msg.role
        content = msg.parts[0]["text"]
        prefix = "使用者：" if role == "user" else "系統："
        prompt += f"{prefix}{content}\n"
    return prompt


def qa_chain(question: str) -> str:
    # 檢查向量庫是否可用
    if retriever is None:
        return f"""您好，很抱歉系統暫時無法查詢相關資料。

問題：{question}

請稍後再試，或聯繫客服人員協助。謝謝您的耐心！"""

    try:
        docs: list[Document] = retriever.get_relevant_documents(question)
        context = "\n\n".join(
            [
                f"[第 {doc.metadata.get('page_number', '?')} 頁]\n{doc.page_content}"
                for doc in docs
            ]
        )
        prompt = f"""你是一位親切且專業的健身客服助理，請用溫暖、鼓勵的語氣回覆用戶，只可以回答與健身相關的問題。

                        文件內容如下：
                        ---
                        {context}
                        ---

                        問題：{question}

                        請以繁體中文簡潔、友善地作答。
                        範例：「您好，很高興為您解答！...祝您順心如意！」
                    """
        return prompt

    except Exception as e:
        print(f"檢索文檔時發生錯誤: {e}")
        return f"""您好，很抱歉在查詢相關資料時遇到問題。

                    問題：{question}

                    請稍後再試，或聯繫客服人員協助。謝謝您的理解！
                """


def call_vllm(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="TheBloke/Qwen2-7B-Chat-AWQ",
        messages=[
            {
                "role": "system",
                "content": "你是一位親切且專業的健身客服助理，請用溫暖、鼓勵的語氣回覆用戶，只可以回答與健身相關的問題。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response["choices"][0]["message"]["content"]


@app.get("/health")
def health_check():
    """健康檢查端點"""
    status = {
        "api": "ok",
        "vectordb": "ok" if vectordb is not None else "error",
        "retriever": "ok" if retriever is not None else "error",
        "mode": "local" if USE_LOCAL_MODE else "server",
        "collection": COLLECTION_NAME,
    }

    # 檢查向量庫中是否有數據
    if vectordb is not None:
        try:
            # 嘗試進行一個簡單的搜索來驗證
            test_docs = retriever.get_relevant_documents("測試", k=1)
            status["documents_count"] = len(test_docs)
            status["has_data"] = len(test_docs) > 0
        except Exception as e:
            status["vectordb"] = "error"
            status["error"] = str(e)

    return status


# 文檔索引管理函數
def load_document_index():
    """載入文檔索引"""
    index_file = "./qdrant_data/doc_index.json"
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_document_index(doc_index):
    """保存文檔索引"""
    os.makedirs("./qdrant_data", exist_ok=True)
    index_file = "./qdrant_data/doc_index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(doc_index, f, ensure_ascii=False, indent=2)


def add_document_to_vectorstore(
    file_path: str, original_name: str, use_ocr: bool = False
):
    """添加文檔到向量庫"""
    if vectordb is None:
        raise HTTPException(status_code=500, detail="向量庫未初始化")

    try:
        # 生成文檔 ID
        doc_id = str(uuid.uuid4())

        if use_ocr:
            # 使用 OCR 模式處理文檔
            print(f"使用 OCR 模式處理文檔: {original_name}")
            extracted_texts = document_processor.process_document_with_ocr(
                file_path, original_name
            )

            # 將提取的文字轉換為 Document 對象
            documents = []
            for page_num, text in extracted_texts:
                doc = Document(
                    page_content=text,
                    metadata={
                        "page_number": page_num,
                        "source": original_name,
                        "extraction_method": "ocr",
                    },
                )
                documents.append(doc)

        else:
            # 使用傳統文字提取方法
            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension == ".pdf":
                loader = PyMuPDFLoader(file_path)
            elif file_extension in [".doc", ".docx"]:
                try:
                    # 優先使用 Docx2txtLoader
                    loader = Docx2txtLoader(file_path)
                except Exception as e:
                    print(
                        f"Docx2txtLoader 失敗，嘗試 UnstructuredWordDocumentLoader: {e}"
                    )
                    try:
                        loader = UnstructuredWordDocumentLoader(file_path)
                    except Exception as e2:
                        raise HTTPException(
                            status_code=400, detail=f"無法載入 Word 文檔: {str(e2)}"
                        )
            else:
                raise HTTPException(status_code=400, detail="不支援的文件格式")

            # 載入文檔
            documents = loader.load()

        if not documents:
            raise HTTPException(status_code=400, detail="無法從文檔中提取內容")

        # 分割文檔
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)

        # 為每個分塊添加文檔 ID
        for chunk in chunks:
            chunk.metadata["doc_id"] = doc_id
            chunk.metadata["filename"] = original_name
            chunk.metadata["processing_method"] = "ocr" if use_ocr else "traditional"

        # 添加到向量庫
        vectordb.add_documents(chunks)

        # 更新文檔索引
        doc_index = load_document_index()
        doc_info = {
            "doc_id": doc_id,
            "filename": original_name,
            "file_path": file_path,
            "upload_time": time.time(),
            "chunk_count": len(chunks),
            "processing_method": "ocr" if use_ocr else "traditional",
        }
        doc_index.append(doc_info)
        save_document_index(doc_index)

        print(
            f"成功添加文檔: {original_name} (ID: {doc_id}, 分塊數: {len(chunks)}, 處理方式: {'OCR' if use_ocr else '傳統'})"
        )
        return doc_id

    except Exception as e:
        print(f"添加文檔失敗: {e}")
        raise HTTPException(status_code=500, detail=f"處理文檔失敗: {str(e)}")


@app.post("/ingest")
def ingest_document(request: IngestRequest):
    """處理上傳的文檔並添加到向量庫"""
    try:
        # 檢查文件是否存在
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        # 檢查文件類型
        allowed_extensions = [".pdf", ".doc", ".docx"]
        file_extension = os.path.splitext(request.file_path)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="不支援的文件格式")

        # 添加文檔到向量庫
        doc_id = add_document_to_vectorstore(
            request.file_path, request.original_name, request.use_ocr
        )

        return {
            "message": "文檔處理成功",
            "doc_id": doc_id,
            "filename": request.original_name,
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"處理文檔時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"處理文檔失敗: {str(e)}")


@app.get("/documents")
def list_documents():
    """獲取所有已上傳的文檔列表"""
    try:
        doc_index = load_document_index()

        # 格式化文檔信息
        documents = []
        for doc in doc_index:
            upload_date = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(doc["upload_time"])
            )
            documents.append(
                {
                    "doc_id": doc["doc_id"],
                    "filename": doc["filename"],
                    "upload_date": upload_date,
                    "chunk_count": doc["chunk_count"],
                }
            )

        return {"documents": documents, "total_count": len(documents)}

    except Exception as e:
        print(f"獲取文檔列表失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取文檔列表失敗")


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """刪除指定的文檔"""
    try:
        if vectordb is None or qdrant_client is None:
            raise HTTPException(status_code=500, detail="向量庫未初始化")

        # 載入文檔索引
        doc_index = load_document_index()
        target_doc = next((doc for doc in doc_index if doc["doc_id"] == doc_id), None)

        if not target_doc:
            raise HTTPException(status_code=404, detail="文檔不存在")

        # 從向量庫中刪除
        qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.doc_id", match=MatchValue(value=doc_id)
                    )
                ]
            ),
        )

        # 更新文檔索引
        remaining_docs = [doc for doc in doc_index if doc["doc_id"] != doc_id]
        save_document_index(remaining_docs)

        # 刪除原始文件（可選）
        try:
            if os.path.exists(target_doc["file_path"]):
                os.remove(target_doc["file_path"])
        except Exception as e:
            print(f"刪除原始文件失敗: {e}")

        return {"message": f"成功刪除文檔: {target_doc['filename']}", "doc_id": doc_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"刪除文檔失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除文檔失敗: {str(e)}")


@app.post("/ask")
def ask(input: AskRequest):
    prompt = build_prompt(input.messages)
    qa_prompt = qa_chain(prompt)
    answer = call_vllm(qa_prompt)
    return {"text": answer}


@app.post("/ask-image")
def ask_image(request: ImageQuestionRequest):
    """處理圖片問答請求"""
    try:
        if not os.path.exists(request.image_path):
            raise HTTPException(status_code=404, detail="圖片文件不存在")

        # 使用多模態模型分析器材圖片
        answer = multimodal_service.analyze_equipment_image(
            request.image_path, request.question
        )

        return {"text": answer}

    except Exception as e:
        print(f"圖片問答失敗: {e}")
        raise HTTPException(status_code=500, detail=f"處理圖片問答失敗: {str(e)}")


@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """上傳圖片文件"""
    try:
        # 檢查文件類型
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="只支援圖片文件")

        # 創建上傳目錄
        upload_dir = "./uploads/images"
        os.makedirs(upload_dir, exist_ok=True)

        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return {
            "message": "圖片上傳成功",
            "file_path": file_path,
            "original_name": file.filename,
        }

    except Exception as e:
        print(f"圖片上傳失敗: {e}")
        raise HTTPException(status_code=500, detail=f"圖片上傳失敗: {str(e)}")


@app.post("/ocr-extract")
def ocr_extract(request: ImageQuestionRequest):
    """從圖片中提取文字"""
    try:
        if not os.path.exists(request.image_path):
            raise HTTPException(status_code=404, detail="圖片文件不存在")

        # 使用多模態模型進行 OCR
        extracted_text = multimodal_service.extract_text_from_image(request.image_path)

        return {"text": extracted_text, "image_path": request.image_path}

    except Exception as e:
        print(f"OCR 文字提取失敗: {e}")
        raise HTTPException(status_code=500, detail=f"OCR 文字提取失敗: {str(e)}")


LINE_REPLY_ENDPOINT = "https://api.line.me/v2/bot/message/reply"
LINE_CHANNEL_ACCESS_TOKEN = "0o0zfZYISsAX7/A1dSh0A5GQD0bnaAJASDR3OkGL9wJAzra0cIq5ofHvfpeU1izkahQlWq83PUZS8hNNUPhbObT6gjmM1UTMc0KnRsVhsxicw/EIrAd7H5yVWfYqUQ9ajW+Q6/obz6LUKADBSBngxwdB04t89/1O/w1cDnyilFU="


@app.post("/webhook")
async def line_webhook(request: Request):
    body = await request.json()
    events = body.get("events", [])
    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_text = event["message"]["text"]
            reply_token = event["replyToken"]

            prompt = build_prompt(
                [
                    Message(
                        id="1", role="user", parts=[{"type": "text", "text": user_text}]
                    )
                ]
            )
            qa_prompt = qa_chain(prompt)
            answer = call_vllm(qa_prompt)

            headers = {
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
            payload = {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": answer}],
            }
            async with httpx.AsyncClient() as client:
                await client.post(LINE_REPLY_ENDPOINT, headers=headers, json=payload)
    return "ok"
