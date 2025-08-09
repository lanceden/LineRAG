from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import uuid
import time
import os
import json

# Qdrant 配置
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "documents"
USE_LOCAL_MODE = True  # 設為 True 使用本地文件模式，False 使用服務器模式

# 1. 初始化 Qdrant 客戶端和向量庫
embedding = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3", encode_kwargs={"normalize_embeddings": True}
)

# 初始化 Qdrant 客戶端
if USE_LOCAL_MODE:
    # 本地文件模式 - 不需要 Docker
    qdrant_client = QdrantClient(path="./local_qdrant")
    print("使用本地文件模式 (無需 Docker)")
else:
    # 服務器模式 - 需要 Qdrant 服務運行
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print(f"使用服務器模式 ({QDRANT_HOST}:{QDRANT_PORT})")

# 確保集合存在
try:
    # 檢查集合是否存在
    collections = qdrant_client.get_collections()
    collection_exists = any(col.name == COLLECTION_NAME for col in collections.collections)
    
    if not collection_exists:
        # 創建集合（假設 embedding 維度為 1024，根據 BAAI/bge-m3 模型）
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
        print(f"創建新的 Qdrant 集合: {COLLECTION_NAME}")
    
    # 初始化向量庫
    vectorstore = Qdrant(
        client=qdrant_client,
        collection_name=COLLECTION_NAME,
        embeddings=embedding
    )
    print("成功連接到 Qdrant 向量庫")
except Exception as e:
    print(f"Qdrant 初始化失敗: {e}")
    if USE_LOCAL_MODE:
        print("本地模式初始化失敗，請檢查文件權限和磁盤空間")
    else:
        print("請確保 Qdrant 服務正在運行:")
        print("Docker: docker run -p 6333:6333 qdrant/qdrant")
        print("或下載二進制文件直接運行")
    vectorstore = None

def add_document(file_path):
    """新增文檔到向量庫"""
    filename = os.path.basename(file_path)
    
    # 生成文檔唯一ID和時間戳
    doc_id = str(uuid.uuid4())
    upload_time = int(time.time())
    
    # 載入文檔索引
    doc_index = load_document_index()
    
    # 檢查是否已存在相同檔案
    for existing_doc in doc_index:
        if existing_doc["filename"] == filename:
            print(f"文檔 {filename} 已存在，doc_id: {existing_doc['doc_id']}")
            return existing_doc["doc_id"]
    
    # 載入 PDF 並切割
    loader = PyMuPDFLoader(file_path)
    docs = loader.load()  # docs = List[Document]，含 .page_content 與 .metadata["page"]

    # 加入完整 metadata
    for doc in docs:
        doc.metadata["doc_id"] = doc_id              # 文檔唯一ID
        doc.metadata["filename"] = filename          # 檔案名
        doc.metadata["source"] = file_path           # 完整路徑
        doc.metadata["upload_time"] = upload_time    # 上傳時間戳
        doc.metadata["page_number"] = doc.metadata.get("page", -1) + 1  # 人類頁碼
    
    # 切割文檔
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(docs)
    
    # 添加文檔到 Qdrant 向量庫
    global vectorstore
    if vectorstore:
        vectorstore.add_documents(chunks)
    else:
        print("向量庫未初始化，請檢查 Qdrant 連接")
        return None
    
    # 更新文檔索引
    doc_info = {
        "doc_id": doc_id,
        "filename": filename,
        "file_path": file_path,
        "upload_time": upload_time,
        "chunk_count": len(chunks)
    }
    doc_index.append(doc_info)
    save_document_index(doc_index)
    
    print(f"成功新增文檔: {filename}, doc_id: {doc_id}")
    return doc_id

def load_document_index():
    """載入文檔索引"""
    index_file = "./qdrant_data/doc_index.json"
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_document_index(doc_index):
    """儲存文檔索引"""
    os.makedirs("./qdrant_data", exist_ok=True)
    index_file = "./qdrant_data/doc_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(doc_index, f, ensure_ascii=False, indent=2)

def delete_document(doc_id):
    """刪除指定文檔"""
    global vectorstore, qdrant_client
    
    # 載入文檔索引
    doc_index = load_document_index()
    
    # 找到要刪除的文檔
    target_doc = None
    for doc in doc_index:
        if doc["doc_id"] == doc_id:
            target_doc = doc
            break
    
    if not target_doc:
        print(f"找不到文檔 ID: {doc_id}")
        return False
    
    print(f"正在刪除文檔: {target_doc['filename']}")
    
    try:
        # 使用 Qdrant 的過濾功能刪除特定文檔的所有向量
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # 刪除所有 doc_id 匹配的點
        qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.doc_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            )
        )
        
        # 更新文檔索引（移除已刪除的文檔）
        remaining_docs = [doc for doc in doc_index if doc["doc_id"] != doc_id]
        save_document_index(remaining_docs)
        
        print(f"成功刪除文檔: {target_doc['filename']}")
        return True
        
    except Exception as e:
        print(f"刪除文檔失敗: {e}")
        return False

def list_documents():
    """列出所有文檔"""
    doc_index = load_document_index()
    if not doc_index:
        print("向量庫中沒有文檔")
        return []
    
    print("向量庫中的文檔:")
    for doc in doc_index:
        upload_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(doc['upload_time']))
        print(f"- {doc['filename']} (ID: {doc['doc_id'][:8]}..., 上傳時間: {upload_date}, 分塊數: {doc['chunk_count']})")
    
    return doc_index

# 使用範例
if __name__ == "__main__":
    # 新增文檔
    # doc_id = add_document("你的新檔案.pdf")
    
    # 列出所有文檔
    # list_documents()
    
    # 刪除文檔
    # delete_document(doc_id)
    pass
