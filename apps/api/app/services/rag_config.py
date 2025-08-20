"""
RAG-Anything 配置管理
"""

import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class RAGConfig:
    """RAG-Anything 配置管理"""

    def __init__(self, company_id: str = None):
        self.company_id = company_id
        self._original_env = {}

    @property
    def openai_api_key(self) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        return api_key

    @property
    def openai_base_url(self) -> str:
        return os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    @property
    def working_dir(self) -> str:
        base_dir = os.getenv("RAG_WORKING_DIR", "./rag_storage")
        if self.company_id:
            # 為每個公司創建獨立的工作目錄
            company_dir = f"{base_dir}/company_{self.company_id}"
            return company_dir
        return base_dir

    @property
    def qdrant_host(self) -> str:
        return os.getenv("QDRANT_HOST", "localhost")

    @property
    def qdrant_port(self) -> int:
        return int(os.getenv("QDRANT_PORT", "6333"))

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    @property
    def neo4j_uri(self) -> str:
        return os.getenv("NEO4J_URI", "bolt://localhost:7687")

    @property
    def neo4j_username(self) -> str:
        return os.getenv("NEO4J_USERNAME", "neo4j")

    @property
    def neo4j_password(self) -> str:
        return os.getenv("NEO4J_PASSWORD", "linerag123")

    def get_company_workspace(self, company_id: str = None) -> str:
        """取得公司工作空間名稱"""
        target_company_id = company_id or self.company_id
        if target_company_id:
            return f"company_{target_company_id}"
        return "default"

    def set_company_namespace(self, company_id: str):
        """設定公司特定的命名空間"""
        company_workspace = self.get_company_workspace(company_id)

        # 保存原始環境變數
        self._original_env = {
            "QDRANT_WORKSPACE": os.environ.get("QDRANT_WORKSPACE"),
            "NEO4J_WORKSPACE": os.environ.get("NEO4J_WORKSPACE"),
        }

        # 設定新的命名空間
        os.environ["QDRANT_WORKSPACE"] = company_workspace
        os.environ["NEO4J_WORKSPACE"] = company_workspace
        os.environ["QDRANT_URL"] = self.qdrant_url

        return company_workspace

    def restore_namespace(self):
        """恢復原始命名空間"""
        for key, value in self._original_env.items():
            if value:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]
        self._original_env.clear()

    def ensure_working_dir(self) -> Path:
        """確保工作目錄存在"""
        working_dir = Path(self.working_dir)
        working_dir.mkdir(parents=True, exist_ok=True)
        return working_dir

    def get_company_output_dir(
        self, company_id: str, base_output_dir: str = "./output"
    ) -> Path:
        """取得公司專用輸出目錄"""
        company_output_dir = Path(base_output_dir) / f"company_{company_id}"
        company_output_dir.mkdir(parents=True, exist_ok=True)
        return company_output_dir

    def get_llm_config(self) -> Dict[str, Any]:
        """取得 LLM 配置"""
        return {
            "model": "gpt-4o-mini",
            "api_key": self.openai_api_key,
            "base_url": self.openai_base_url,
        }

    def get_vision_model_config(self) -> Dict[str, Any]:
        """取得視覺模型配置"""
        return {
            "model": "gpt-4o",
            "api_key": self.openai_api_key,
            "base_url": self.openai_base_url,
        }

    def get_embedding_config(self) -> Dict[str, Any]:
        """取得嵌入模型配置"""
        return {
            "model": "text-embedding-3-large",
            "api_key": self.openai_api_key,
            "base_url": self.openai_base_url,
            "embedding_dim": 3072,
            "max_token_size": 8192,
        }

    def get_rerank_config(self) -> Dict[str, Any]:
        """取得重排序模型配置"""
        return {
            "model": "BAAI/bge-reranker-v2-m3",
            "api_key": self.openai_api_key,
            "base_url": self.openai_base_url,
            "top_n": 10,
        }

    def print_config_summary(self):
        """打印配置摘要"""
        print("🔧 RAG-Anything 配置摘要:")
        print(f"   📁 工作目錄: {self.working_dir}")
        print(f"   🏢 公司ID: {self.company_id}")
        if self.company_id:
            print(f"   🏷️  工作空間: {self.get_company_workspace()}")
        print(f"   📊 Qdrant: {self.qdrant_host}:{self.qdrant_port}")
        print(f"   🔗 Neo4j: {self.neo4j_uri}")
        print(f"   🤖 OpenAI Base URL: {self.openai_base_url}")
