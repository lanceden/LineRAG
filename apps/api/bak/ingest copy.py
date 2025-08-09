from langchain.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import uuid
import time
import os
import json

# 1. 載入舊向量庫
embedding = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3", encode_kwargs={"normalize_embeddings": True}
)
try:
    vectorstore = FAISS.load_local("./vectorstore", embedding)
except:
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
    
    # 載入或創建向量庫
    global vectorstore
    if vectorstore:
        vectorstore.add_documents(chunks)
    else:
        vectorstore = FAISS.from_documents(chunks, embedding)
    
    # 儲存向量庫
    vectorstore.save_local("./vectorstore")
    
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
    index_file = "./vectorstore/doc_index.json"
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_document_index(doc_index):
    """儲存文檔索引"""
    os.makedirs("./vectorstore", exist_ok=True)
    index_file = "./vectorstore/doc_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(doc_index, f, ensure_ascii=False, indent=2)

def delete_document(doc_id):
    """刪除指定文檔"""
    global vectorstore
    
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
    
    # 由於 FAISS 不支援直接刪除，需要重建向量庫
    print(f"正在刪除文檔: {target_doc['filename']}")
    
    # 載入所有文檔，排除要刪除的
    all_chunks = []
    remaining_docs = [doc for doc in doc_index if doc["doc_id"] != doc_id]
    
    for doc_info in remaining_docs:
        # 重新載入每個保留的文檔
        try:
            loader = PyMuPDFLoader(doc_info["file_path"])
            docs = loader.load()
            
            # 重新加入 metadata（保持原有的 doc_id）
            for doc in docs:
                doc.metadata["doc_id"] = doc_info["doc_id"]
                doc.metadata["filename"] = os.path.basename(doc_info["file_path"])
                doc.metadata["source"] = doc_info["file_path"]
                doc.metadata["upload_time"] = doc_info["upload_time"]
                doc.metadata["page_number"] = doc.metadata.get("page", -1) + 1
            
            # 切割文檔
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = text_splitter.split_documents(docs)
            all_chunks.extend(chunks)
            
        except Exception as e:
            print(f"重新載入文檔 {doc_info['filename']} 失敗: {e}")
            continue
    
    # 重建向量庫
    if all_chunks:
        vectorstore = FAISS.from_documents(all_chunks, embedding)
        vectorstore.save_local("./vectorstore")
    else:
        # 如果沒有剩餘文檔，刪除向量庫
        import shutil
        if os.path.exists("./vectorstore"):
            shutil.rmtree("./vectorstore")
        vectorstore = None
    
    # 更新文檔索引
    save_document_index(remaining_docs)
    
    print(f"成功刪除文檔: {target_doc['filename']}")
    return True

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
