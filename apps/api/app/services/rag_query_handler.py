"""
RAG-Anything 查詢處理器
"""

import asyncio
import os
import time

from typing import List, Dict, Any
from .rag_config import RAGConfig
from .rag_database_manager import DatabaseManager
from app.utils.namespace import AsyncNamespaceContext
from app.utils.data_validator import verify_query_data_exists

# 中文註解：公司級資料健檢結果快取（避免每次打 DB），TTL 預設 10 分鐘
_CHECK_CACHE_TTL_SECONDS = int(os.getenv("QUERY_CHECK_TTL", "600"))
_company_check_cache: Dict[int, float] = {}


def _should_skip_precheck(company_id: int) -> bool:
    # 中文註解：若公司有快取且未過期，則跳過資料健檢
    ts = _company_check_cache.get(company_id)
    if ts is None:
        return False
    return (time.time() - ts) < _CHECK_CACHE_TTL_SECONDS


def _mark_precheck(company_id: int):
    # 中文註解：記錄該公司最後一次資料健檢時間
    _company_check_cache[company_id] = time.time()


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
            # 直接處理查詢，不使用異步上下文管理器
            if company_id:
                t0 = time.time()
                # 查詢前驗證數據存在（加入公司級快取，預設 10 分鐘）
                if not _should_skip_precheck(int(company_id)):
                    data_exists = await verify_query_data_exists(int(company_id))
                    if not data_exists:
                        raise ValueError(f"No data found for company {company_id}")
                    _mark_precheck(int(company_id))
                    print(f"⏱️ Precheck 耗時: {time.time() - t0:.2f}s")
                else:
                    print("⏭️ 跳過資料健檢（公司級快取尚有效）")
                t1 = time.time()

                # 動態獲取當前公司的 RAG-Anything 實例
                print(f"🔧 為公司 {company_id} 動態創建/取得 RAG 查詢實例...")
                rag_instance = await self.rag_service.get_rag_instance_for_company(
                    str(company_id)
                )
                print(f"⏱️ 取得查詢實例耗時: {time.time() - t1:.2f}s")

                # 執行查詢
                print(f"🚀 執行 RAG 查詢...")
                t2 = time.time()
                
                # 支援環境變數覆蓋查詢模式，提升性能測試靈活性
                import os
                effective_mode = os.getenv("RAG_QUERY_MODE", mode)
                print(f"🔧 使用查詢模式: {effective_mode} (原始: {mode})")
                
                result = await rag_instance.aquery(
                    query, mode=effective_mode, enable_rerank=False
                )
                print(f"⏱️ aquery 耗時: {time.time() - t2:.2f}s")

                print(f"✅ RAG 查詢完成 (總耗時: {time.time() - t0:.2f}s)")
                print(f"   結果長度: {len(result)} 字符")
                print(f"   結果預覽: {result[:100]}...")
                print("=" * 80)

                return result
            else:
                # 沒有指定公司ID的查詢 - 使用默認實例
                print(f"🚀 執行 RAG 查詢 (無公司限制)...")
                rag_instance = await self.rag_service.get_rag_instance_for_company(
                    "default"
                )
                # 支援環境變數覆蓋查詢模式
                import os
                effective_mode = os.getenv("RAG_QUERY_MODE", mode)
                print(f"🔧 使用查詢模式: {effective_mode} (原始: {mode})")
                
                # 啟用重排序功能以提升結果質量
                result = await rag_instance.aquery(
                    query, mode=effective_mode, enable_rerank=False
                )
                print(f"✅ RAG 查詢完成")
                return result

        except Exception as e:
            print(f"❌ RAG 查詢失敗: {str(e)}")
            print("=" * 80)
            raise Exception(f"Query failed: {str(e)}")

    async def query_multimodal(
        self,
        query: str,
        multimodal_content: List[Dict],
        mode: str = "hybrid",
        company_id: str = None,
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
            # 查詢前檢查數據庫狀態
            await self._check_database_status_before_query(query, company_id)

            # 動態創建或獲取 RAG 實例
            if company_id:
                # 為特定公司創建 RAG 實例
                rag_instance = await self.rag_service.get_rag_instance_for_company(
                    str(company_id)
                )

                print(f"🚀 執行多模態 RAG 查詢...")
                # 啟用重排序功能以提升結果質量
                result = await rag_instance.aquery_with_multimodal(
                    query=query, multimodal_content=multimodal_content, mode=mode
                )
            else:
                # 沒有指定公司ID的查詢
                rag_instance = await self.rag_service.get_rag_instance_for_company(
                    "default"
                )
                print(f"🚀 執行多模態 RAG 查詢 (無公司限制)...")
                result = await rag_instance.aquery_with_multimodal(
                    query=query, multimodal_content=multimodal_content, mode=mode
                )

            print(f"✅ 多模態 RAG 查詢完成")
            print(f"   結果長度: {len(result)} 字符")
            print("=" * 80)

            return result

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

    async def _check_database_status_before_query(
        self, query: str, company_id: str = None
    ):
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
                print(
                    f"   ❌ Qdrant 檢查失敗: {qdrant_status.get('message', 'Unknown error')}"
                )

            # 檢查 Neo4j 數據
            neo4j_status = status.get("neo4j", {})
            if neo4j_status.get("status") == "success":
                total_nodes = neo4j_status.get("total_nodes", 0)
                print(f"   🔗 Neo4j: {total_nodes} 個節點")
                if total_nodes == 0:
                    print(f"   ⚠️  警告: 命名空間中沒有圖節點，可能導致查詢無結果")
            else:
                print(
                    f"   ❌ Neo4j 檢查失敗: {neo4j_status.get('message', 'Unknown error')}"
                )
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
