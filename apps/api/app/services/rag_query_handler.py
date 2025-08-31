"""
RAG-Anything 查詢處理器
"""

import asyncio
import os
import time
import hashlib
from functools import lru_cache
from typing import List, Dict, Any, Optional
from .rag_config import RAGConfig
from .rag_database_manager import DatabaseManager
from app.utils.namespace import AsyncNamespaceContext
from app.utils.data_validator import verify_query_data_exists

# 中文註解：公司級資料健檢結果快取（避免每次打 DB），TTL 預設 10 分鐘
_CHECK_CACHE_TTL_SECONDS = int(os.getenv("QUERY_CHECK_TTL", "600"))
_company_check_cache: Dict[int, float] = {}

# 查詢結果快取
_QUERY_CACHE_TTL_SECONDS = int(os.getenv("QUERY_CACHE_TTL", "300"))  # 5分鐘
_query_result_cache: Dict[str, Dict[str, Any]] = {}


def _should_skip_precheck(company_id: int) -> bool:
    # 中文註解：若公司有快取且未過期，則跳過資料健檢
    ts = _company_check_cache.get(company_id)
    if ts is None:
        return False
    return (time.time() - ts) < _CHECK_CACHE_TTL_SECONDS


def _mark_precheck(company_id: int):
    # 中文註解：記錄該公司最後一次資料健檢時間
    _company_check_cache[company_id] = time.time()


def _get_query_hash(query: str, company_id: str, mode: str) -> str:
    """生成查詢雜湊用於快取"""
    content = f"{query}:{company_id}:{mode}"
    return hashlib.md5(content.encode()).hexdigest()


def _is_cache_valid(cache_entry: Dict[str, Any]) -> bool:
    """檢查快取是否有效"""
    if "timestamp" not in cache_entry:
        return False
    return (time.time() - cache_entry["timestamp"]) < _QUERY_CACHE_TTL_SECONDS


def _cleanup_expired_cache():
    """清理過期的快取項目"""
    current_time = time.time()
    expired_keys = [
        key
        for key, entry in _query_result_cache.items()
        if current_time - entry.get("timestamp", 0) > _QUERY_CACHE_TTL_SECONDS
    ]
    for key in expired_keys:
        del _query_result_cache[key]
    if expired_keys:
        print(f"🧹 清理了 {len(expired_keys)} 個過期查詢快取")


class QueryHandler:
    """查詢處理器"""

    def __init__(self, rag_service, config: RAGConfig, db_manager: DatabaseManager):
        self.rag_service = rag_service  # 使用服務引用而不是實例
        self.config = config
        self.db_manager = db_manager
        self.api_call_count = 0
        self.api_error_count = 0

        # 效能監控
        self.query_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0.0,
            "slow_queries": 0,
        }

    async def query_with_cache(
        self, query: str, mode: str = "naive", company_id: str = None
    ) -> str:
        """帶快取的查詢方法"""
        start_time = time.time()
        self.query_stats["total_queries"] += 1

        # 生成查詢雜湊
        query_hash = _get_query_hash(query, company_id or "", mode)

        # 檢查快取
        if query_hash in _query_result_cache:
            cache_entry = _query_result_cache[query_hash]
            if _is_cache_valid(cache_entry):
                self.query_stats["cache_hits"] += 1
                response_time = time.time() - start_time
                self._update_response_time(response_time)
                print(f"⚡ 快取命中，節省查詢時間")
                return cache_entry["result"]

        # 快取未命中，執行實際查詢
        self.query_stats["cache_misses"] += 1
        print(f"🔍 快取未命中，執行新查詢")

        result = await self._execute_query(query, mode, company_id)

        # 儲存到快取
        _query_result_cache[query_hash] = {
            "result": result,
            "timestamp": time.time(),
            "query": query,
            "mode": mode,
            "company_id": company_id,
        }

        # 定期清理過期快取
        if len(_query_result_cache) > 1000:  # 快取大小限制
            _cleanup_expired_cache()

        response_time = time.time() - start_time
        self._update_response_time(response_time)

        if response_time > 5.0:  # 慢查詢閾值
            self.query_stats["slow_queries"] += 1
            print(f"🐌 慢查詢警告: {response_time:.2f}s")

        return result

    def _update_response_time(self, response_time: float):
        """更新平均響應時間"""
        total_queries = self.query_stats["total_queries"]
        current_avg = self.query_stats["avg_response_time"]
        self.query_stats["avg_response_time"] = (
            (current_avg * (total_queries - 1)) + response_time
        ) / total_queries

    async def _execute_query(
        self, query: str, mode: str = "naive", company_id: str = None
    ) -> str:
        """實際執行查詢的內部方法"""
        if company_id:
            # 驗證資料存在
            if not _should_skip_precheck(int(company_id)):
                data_exists = await verify_query_data_exists(int(company_id))
                if not data_exists:
                    raise ValueError(f"No data found for company {company_id}")
                _mark_precheck(int(company_id))

            # 獲取 RAG 實例
            rag_instance = await self.rag_service.get_rag_instance_for_company(
                company_id
            )

            # 確保內容已載入
            await self._ensure_company_content_loaded(company_id, rag_instance)

            # 執行查詢
            result = await rag_instance.aquery(query, mode=mode, enable_rerank=False)

            return result
        else:
            raise ValueError("Query requires company_id")

    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取效能統計資訊"""
        cache_hit_rate = (
            self.query_stats["cache_hits"]
            / max(self.query_stats["total_queries"], 1)
            * 100
        )

        return {
            **self.query_stats,
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "cache_size": len(_query_result_cache),
            "active_cache_entries": len(
                [k for k, v in _query_result_cache.items() if _is_cache_valid(v)]
            ),
        }

    async def smart_query_mode(self, query: str) -> str:
        """智慧選擇查詢模式"""
        query_lower = query.lower()

        # 簡單查詢用 naive
        if len(query.split()) < 5:
            return "naive"

        # 複雜查詢用 hybrid
        complex_keywords = ["比較", "差異", "如何", "為什麼", "原因", "影響"]
        if any(keyword in query_lower for keyword in complex_keywords):
            return "hybrid"

        # 預設用 local
        return "local"

    async def query_text(
        self, query: str, mode: str = "hybrid", company_id: str = None
    ) -> str:
        """純文本查詢 - 現在使用智慧快取"""
        print("=" * 80)
        print(f"🔍 開始 RAG 文本查詢")
        print(f"   查詢內容: {query}")
        print(f"   原始模式: {mode}")
        print(f"   公司ID: {company_id}")
        print("=" * 80)

        try:
            # 使用智慧模式選擇
            smart_mode = await self.smart_query_mode(query)
            if smart_mode != mode:
                print(f"🧠 智慧模式選擇: {mode} → {smart_mode}")

            # 使用帶快取的查詢
            result = await self.query_with_cache(query, smart_mode, company_id)

            print(f"✅ RAG 查詢完成")
            print(f"   最終模式: {smart_mode}")
            print(f"   結果長度: {len(result)} 字符")
            print(f"   效能統計: {self.get_performance_stats()}")
            print("=" * 80)

            return result

        except Exception as e:
            print(f"❌ RAG 查詢失敗: {str(e)}")
            print("=" * 80)
            raise Exception(f"Text query failed: {str(e)}")

        except Exception as e:
            print(f"❌ RAG 查詢失敗: {str(e)}")
            print("=" * 80)
            raise Exception(f"Query failed: {str(e)}")

    async def _ensure_company_content_loaded(self, company_id: str, rag_instance):
        """確保公司所有文檔的 content_list 已載入 RAG (版本檢查機制)"""
        try:
            # 檢查 kv_store_parse_cache.json 的修改時間
            import os
            import json
            from pathlib import Path

            cache_file = Path(
                f"./rag_storage/company_{company_id}/kv_store_parse_cache.json"
            )
            if not cache_file.exists():
                print(f"⚠️ 解析快取檔案不存在: {cache_file}")
                return

            cache_file_mtime = os.path.getmtime(cache_file)

            # 檢查 RAG 實例是否有記錄最後載入時間
            if not hasattr(rag_instance, "_last_loaded_time"):
                rag_instance._last_loaded_time = 0
                print(f"🔍 首次載入公司 {company_id} 的文檔...")
            elif cache_file_mtime <= rag_instance._last_loaded_time:
                print(
                    f"⏭️ 快取檔案未更新，跳過載入 (快取時間: {cache_file_mtime}, 上次載入: {rag_instance._last_loaded_time})"
                )
                return
            else:
                print(
                    f"🔄 檢測到快取檔案更新，重新載入文檔 (快取時間: {cache_file_mtime} > 上次載入: {rag_instance._last_loaded_time})"
                )

            # 2. 查資料庫取回公司所有的文檔
            from app.core.database import SessionLocal
            from app.models.document import DocumentMetadata

            db = SessionLocal()
            try:
                company_docs = (
                    db.query(DocumentMetadata)
                    .filter(
                        DocumentMetadata.company_id == int(company_id),
                        DocumentMetadata.processing_status == "completed",
                    )
                    .all()
                )

                print(f"📊 找到 {len(company_docs)} 個已完成的文檔")

                if not company_docs:
                    print("⚠️ 公司沒有已完成的文檔")
                    return

                # 3. 讀取 kv_store_parse_cache.json
                with open(cache_file, "r", encoding="utf-8") as f:
                    parse_cache = json.load(f)

                print(f"📄 載入解析快取，共 {len(parse_cache)} 個項目")

                # 4. 對每個文檔執行 insert_content_list
                loaded_count = 0
                for doc in company_docs:
                    lightrag_doc_id = doc.lightrag_doc_id
                    if not lightrag_doc_id:
                        continue

                    # 在 parse_cache 中找到對應的 content_list
                    cache_entry = None
                    for cache_key, cache_data in parse_cache.items():
                        if cache_data.get("doc_id") == lightrag_doc_id:
                            cache_entry = cache_data
                            break

                    if not cache_entry:
                        print(f"⚠️ 找不到 {lightrag_doc_id} 的解析快取")
                        continue

                    content_list = cache_entry.get("content_list", [])
                    if not content_list:
                        print(f"⚠️ {doc.original_filename} 的 content_list 為空")
                        continue

                    print(
                        f"📝 載入 {doc.original_filename} 的 content_list ({len(content_list)} 項)"
                    )

                    # 使用 insert_content_list 載入到 RAG
                    await rag_instance.insert_content_list(
                        content_list=content_list,
                        file_path=doc.original_filename,
                        doc_id=lightrag_doc_id,
                    )
                    loaded_count += 1

                # 更新最後載入時間
                rag_instance._last_loaded_time = cache_file_mtime
                print(
                    f"✅ 成功載入 {loaded_count} 個文檔到 RAG (更新時間戳: {cache_file_mtime})"
                )

            finally:
                db.close()

        except Exception as e:
            print(f"⚠️ 載入公司文檔時出錯: {e}")
            # 不拋出異常，讓查詢繼續進行

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

                # 將多模態內容整合到查詢中
                multimodal_text = self._format_multimodal_content(multimodal_content)
                enhanced_query = f"{query}\n\n多模態內容:\n{multimodal_text}"

                # 強制使用 naive 模式，避免觸發 MinerU
                safe_mode = "naive"
                print(f"🔧 使用安全查詢模式: {safe_mode} (避免觸發 MinerU)")

                # 創建查詢參數
                from lightrag import QueryParam

                query_param = QueryParam(
                    mode=safe_mode,
                    response_type="Multiple Paragraphs",
                    top_k=10,
                    enable_rerank=False,
                )

                result = await rag_instance.aquery(
                    query=enhanced_query, param=query_param
                )
            else:
                # 多模態查詢必須有公司ID，不允許無公司限制的查詢
                raise ValueError("Multimodal query requires company_id")

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

    def _format_multimodal_content(self, multimodal_content: List[Dict]) -> str:
        """格式化多模態內容為文本"""
        formatted_parts = []

        for i, content in enumerate(multimodal_content):
            content_type = content.get("type", "unknown")

            if content_type == "image":
                # 圖片內容 - 包含描述和base64數據
                description = content.get("description", "圖片內容")
                base64_data = content.get("data", "")
                formatted_parts.append(f"[圖片 {i+1}] {description}")
                if base64_data:
                    formatted_parts.append(f"Base64數據長度: {len(base64_data)} 字符")

            elif content_type == "text":
                # 文本內容
                text_data = content.get("data", "")
                formatted_parts.append(f"[文本 {i+1}] {text_data}")

            else:
                # 其他類型
                data = content.get("data", "")
                formatted_parts.append(f"[{content_type} {i+1}] {str(data)}")

        return "\n".join(formatted_parts)
