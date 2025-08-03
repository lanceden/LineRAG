from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

loader = PyMuPDFLoader("./pdfs/★ 操作手冊〔運動中心〕- 產品設定(含報表分類).pdf")
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(docs)

embedding = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3", encode_kwargs={"normalize_embeddings": True}
)
vectorstore = FAISS.from_documents(chunks, embedding)
vectorstore.save_local("./vectorstore")
