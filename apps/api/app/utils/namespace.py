"""
統一命名空間管理
"""

import os
from typing import Tuple, Optional


def get_company_workspace(company_id: int) -> str:
    """獲取公司的統一命名空間"""
    return f"company_{company_id}"


def set_company_environment(company_id: int) -> Tuple[Optional[str], Optional[str]]:
    """設定公司環境變數，返回原始值"""
    workspace = get_company_workspace(company_id)
    
    # 保存原始環境變數
    original_qdrant = os.environ.get("QDRANT_WORKSPACE")
    original_neo4j = os.environ.get("NEO4J_WORKSPACE")
    
    # 設定新的命名空間
    os.environ["QDRANT_WORKSPACE"] = workspace
    os.environ["NEO4J_WORKSPACE"] = workspace
    
    print(f"🏷️  設定命名空間: {workspace}")
    print(f"   QDRANT_WORKSPACE: {workspace}")
    print(f"   NEO4J_WORKSPACE: {workspace}")
    
    return original_qdrant, original_neo4j


def restore_environment(original_qdrant: Optional[str], original_neo4j: Optional[str]):
    """恢復原始環境變數"""
    if original_qdrant:
        os.environ["QDRANT_WORKSPACE"] = original_qdrant
        print(f"🔄 恢復 QDRANT_WORKSPACE: {original_qdrant}")
    elif "QDRANT_WORKSPACE" in os.environ:
        del os.environ["QDRANT_WORKSPACE"]
        print(f"🔄 清除 QDRANT_WORKSPACE")
        
    if original_neo4j:
        os.environ["NEO4J_WORKSPACE"] = original_neo4j  
        print(f"🔄 恢復 NEO4J_WORKSPACE: {original_neo4j}")
    elif "NEO4J_WORKSPACE" in os.environ:
        del os.environ["NEO4J_WORKSPACE"]
        print(f"🔄 清除 NEO4J_WORKSPACE")


class NamespaceContext:
    """命名空間上下文管理器"""
    
    def __init__(self, company_id: int):
        self.company_id = company_id
        self.original_qdrant = None
        self.original_neo4j = None
    
    def __enter__(self):
        self.original_qdrant, self.original_neo4j = set_company_environment(self.company_id)
        return get_company_workspace(self.company_id)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        restore_environment(self.original_qdrant, self.original_neo4j)


# 異步版本的上下文管理器
class AsyncNamespaceContext:
    """異步命名空間上下文管理器"""
    
    def __init__(self, company_id: int):
        self.company_id = company_id
        self.original_qdrant = None
        self.original_neo4j = None
    
    async def __aenter__(self):
        self.original_qdrant, self.original_neo4j = set_company_environment(self.company_id)
        return get_company_workspace(self.company_id)
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        restore_environment(self.original_qdrant, self.original_neo4j)