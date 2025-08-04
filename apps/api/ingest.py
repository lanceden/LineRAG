from langchain.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. 載入舊的 vectorstore
embedding = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3", encode_kwargs={"normalize_embeddings": True}
)
try:
    vectorstore = FAISS.load_local("./vectorstore", embedding)
except:
    vectorstore = None

# 2. 處理新 PDF
loader = PyMuPDFLoader("你的新檔案.pdf")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(docs)

# 3. 疊加
if vectorstore:
    vectorstore.add_documents(chunks)
else:
    vectorstore = FAISS.from_documents(chunks, embedding)

vectorstore.save_local("./vectorstore")
