"""
RAG-Anything 查詢處理器
"""

import asyncio
from typing import List, Dict, Any
from .rag_config import RAGConfig
from .rag_database_manager import DatabaseManager
from app.utils.namespace import AsyncNamespaceContext
from app.utils.data_validator import verify_query_data_exists


class QueryHandler:
    """查詢處理器"""
    
    def __init__(self, rag_service, config: RAGConfig, db_manager: DatabaseManager):
        self.rag_service = rag_service  # 使用服務引用而不是實例
        self.config = config
        self.db_manager = db_manager
        self.api_call_count = 0
        self.api_error_count = 0

    async def query_text(
        self, query: str, mode: str = "hybrid", company_id: str = None
    ) -> str:
        """純文本查詢"""
        print("=" * 80)
        print(f"🔍 開始 RAG 文本查詢")
        print(f"   查詢內容: {query}")
        print(f"   查詢模式: {mode}")
        print(f"   公司ID: {company_id}")
        print("=" * 80)

        try:
            # 使用異步命名空間上下文管理器
            if company_id:
                async with AsyncNamespaceContext(int(company_id)) as company_workspace:
                    print(f"🏷️  查詢命名空間: {company_workspace}")
                    
                    # 查詢前驗證數據存在
                    data_exists = await verify_query_data_exists(int(company_id))
                    if not data_exists:
                        raise ValueError(f"No data found for company {company_id}")
                    
                    # 查詢前檢查數據庫狀態
                    await self._check_database_status_before_query(query, company_id)

                    print(f"🚀 執行 RAG 查詢...")
                    result = await self.rag_instance.aquery(query, mode=mode)

                    print(f"✅ RAG 查詢完成")
                    print(f"   結果長度: {len(result)} 字符")
                    print(f"   結果預覽: {result[:100]}...")
                    print("=" * 80)

                    return result
            else:
                # 沒有指定公司ID的查詢
                print(f"🚀 執行 RAG 查詢 (無公司限制)...")
                result = await self.rag_instance.aquery(query, mode=mode)
                print(f"✅ RAG 查詢完成")
                return result

        except Exception as e:
            print(f"❌ RAG 查詢失敗: {str(e)}")
            print("=" * 80)
            raise Exception(f"Query failed: {str(e)}")

    async def query_multimodal(
        self, query: str, multimodal_content: List[Dict], mode: str = "hybrid", company_id: str = None
    ) -> str:
        """多模態查詢"""
        print("=" * 80)
        print(f"🔍 開始 RAG 多模態查詢")
        print(f"   查詢內容: {query}")
        print(f"   查詢模式: {mode}")
        print(f"   多模態內容數量: {len(multimodal_content)}")
        print(f"   公司ID: {company_id}")
        print("=" * 80)

        try:
            # 設定公司命名空間
            if company_id:
                company_workspace = self.config.set_company_namespace(company_id)
                print(f"🏷️  查詢命名空間: {company_workspace}")
            
            try:
                # 查詢前檢查數據庫狀態
                await self._check_database_status_before_query(query, company_id)

                print(f"🚀 執行多模態 RAG 查詢...")
                result = await self.rag_instance.aquery_with_multimodal(
                    query=query, multimodal_content=multimodal_content, mode=mode
                )

                print(f"✅ 多模態 RAG 查詢完成")
                print(f"   結果長度: {len(result)} 字符")
                print("=" * 80)

                return result
                
            finally:
                if company_id:
                    self.config.restore_namespace()

        except Exception as e:
            print(f"❌ 多模態 RAG 查詢失敗: {str(e)}")
            print("=" * 80)
            raise Exception(f"Multimodal query failed: {str(e)}")

    async def robust_openai_call(
        self,
        model: str,
        prompt: str,
        system_prompt: str = None,
        history_messages: List = None,
        **kwargs,
    ) -> str:
        """完整的 OpenAI API 調用（包含錯誤處理和重試）"""
        if history_messages is None:
            history_messages = []
            
        max_retries = 3
        retry_count = 0

        # 獲取 API 配置
        llm_config = self.config.get_llm_config()

        while retry_count < max_retries:
            try:
                self.api_call_count += 1

                # 動態導入避免循環引用
                from lightrag.llm.openai import openai_complete_if_cache

                # 調用 OpenAI API
                result = await openai_complete_if_cache(
                    model,
                    prompt,
                    system_prompt=system_prompt,
                    history_messages=history_messages,
                    api_key=llm_config["api_key"],
                    base_url=llm_config["base_url"],
                    **kwargs,
                )

                return result

            except Exception as e:
                retry_count += 1
                self.api_error_count += 1
                error_msg = str(e)

                # 檢查是否為可重試的錯誤
                if self._is_retryable_error(error_msg) and retry_count < max_retries:
                    wait_time = 2**retry_count  # 指數退避
                    print(
                        f"OpenAI API call failed (attempt {retry_count}/{max_retries}): {error_msg}"
                    )
                    print(f"Retrying in {wait_time} seconds...")

                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # 不可重試的錯誤或達到最大重試次數
                    print(f"OpenAI API call failed permanently: {error_msg}")
                    raise Exception(
                        f"OpenAI API failed after {max_retries} attempts: {error_msg}"
                    )

    def get_api_stats(self) -> Dict[str, Any]:
        """取得 API 使用統計"""
        success_rate = 0
        if self.api_call_count > 0:
            success_rate = (
                (self.api_call_count - self.api_error_count) / self.api_call_count
            ) * 100

        return {
            "total_calls": self.api_call_count,
            "error_count": self.api_error_count,
            "success_count": self.api_call_count - self.api_error_count,
            "success_rate_percent": round(success_rate, 2),
            "service_health": (
                "healthy"
                if success_rate > 95
                else "degraded" if success_rate > 80 else "unhealthy"
            ),
        }

    async def _check_database_status_before_query(self, query: str, company_id: str = None):
        """查詢前檢查數據庫狀態"""
        print(f"🔍 查詢前檢查數據庫狀態...")
        
        if company_id:
            # 檢查特定公司的數據狀態
            status = await self.db_manager.check_company_data_status(company_id)
            
            # 檢查 Qdrant 數據
            qdrant_status = status.get("qdrant", {})
            if qdrant_status.get("status") == "success":
                total_points = qdrant_status.get("total_points", 0)
                print(f"   📊 Qdrant: {total_points} 個向量點")
                if total_points == 0:
                    print(f"   ⚠️  警告: 命名空間中沒有向量數據，可能導致查詢無結果")
            else:
                print(f"   ❌ Qdrant 檢查失敗: {qdrant_status.get('message', 'Unknown error')}")
            
            # 檢查 Neo4j 數據
            neo4j_status = status.get("neo4j", {})
            if neo4j_status.get("status") == "success":
                total_nodes = neo4j_status.get("total_nodes", 0)
                print(f"   🔗 Neo4j: {total_nodes} 個節點")
                if total_nodes == 0:
                    print(f"   ⚠️  警告: 命名空間中沒有圖節點，可能導致查詢無結果")
            else:
                print(f"   ❌ Neo4j 檢查失敗: {neo4j_status.get('message', 'Unknown error')}")
        else:
            # 檢查整體數據庫狀態
            await self.db_manager.check_database_status()

    def _is_retryable_error(self, error_msg: str) -> bool:
        """判斷是否為可重試的錯誤"""
        retryable_errors = [
            "rate limit",
            "timeout",
            "connection",
            "server error",
            "503",
            "502",
            "500",
            "429",
        ]

        error_lower = error_msg.lower()
        return any(err in error_lower for err in retryable_errors)