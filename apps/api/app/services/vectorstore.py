from __future__ import annotations
import os
from typing import Optional
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

# Load .env
from app.core import env


class VectorStoreService:
    def __init__(self):
        self.embedding = None
        self.qdrant_client: Optional[QdrantClient] = None
        self.vectordb: Optional[Qdrant] = None
        self.retriever = None

    def init(self):
        # Initialize embedding
        self.embedding = HuggingFaceEmbeddings(
            model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3"),
            encode_kwargs={"normalize_embeddings": True},
        )
        # Init qdrant client
        use_local_qdrant = os.getenv("USE_LOCAL_QDRANT", "true").lower() in {"1", "true", "yes"}
        if use_local_qdrant:
            self.qdrant_client = QdrantClient(path=os.getenv("QDRANT_PATH", "./local_qdrant"))
        else:
            self.qdrant_client = QdrantClient(
                host=os.getenv("QDRANT_HOST", "localhost"), 
                port=int(os.getenv("QDRANT_PORT", "6333"))
            )
        
        # Create collection if it doesn't exist
        collection_name = os.getenv("COLLECTION_NAME", "documents")
        try:
            collection_info = self.qdrant_client.get_collection(collection_name)
        except Exception:
            # Collection doesn't exist, create it
            from qdrant_client.models import VectorParams, Distance
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)  # bge-m3 has 1024 dimensions
            )
        
        # Wrap langchain Qdrant store
        self.vectordb = Qdrant(client=self.qdrant_client, collection_name=collection_name, embeddings=self.embedding)
        self.retriever = self.vectordb.as_retriever()

    def is_ready(self) -> bool:
        return self.vectordb is not None and self.retriever is not None


vectorstore_service = VectorStoreService()

def get_vectorstore_service() -> VectorStoreService:
    return vectorstore_service
