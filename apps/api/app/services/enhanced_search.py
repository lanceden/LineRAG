"""
增強檢索系統
實現方案A的核心功能：基於標籤的精準檢索與多文檔整合
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from app.services.llm import get_llm_client
from app.services.vectorstore import get_vectorstore_service


@dataclass
class SearchResult:
    """檢索結果"""

    content: str
    score: float
    metadata: Dict
    chunk_id: str
    document_id: str


@dataclass
class QueryAnalysis:
    """查詢分析結果"""

    intent: str  # 查詢意圖
    entities: Dict[str, List[str]]  # 實體識別
    keywords: List[str]  # 關鍵詞
    filters: Dict[str, List[str]]  # 建議的過濾條件


class EnhancedSearchService:
    """增強檢索服務"""

    def __init__(self):
        self.llm_client = get_llm_client()
        self.vectorstore = get_vectorstore_service()

        # 常見查詢意圖分類
        self.intent_categories = [
            "價格查詢",
            "產品功能",
            "使用方法",
            "故障排除",
            "政策說明",
            "流程指引",
            "聯絡資訊",
            "一般問答",
        ]

    async def enhanced_search(
        self, query: str, top_k: int = 10, enable_reranking: bool = True
    ) -> Tuple[List[SearchResult], QueryAnalysis]:
        """
        執行增強檢索

        Args:
            query: 用戶查詢
            top_k: 返回結果數量
            enable_reranking: 是否啟用重排序

        Returns:
            (檢索結果列表, 查詢分析)
        """

        # 1. 分析查詢意圖和實體
        query_analysis = await self._analyze_query(query)

        # 2. 構建檢索過濾條件
        search_filters = self._build_search_filters(query_analysis)

        # 3. 執行向量檢索
        initial_results = await self._vector_search(
            query, filters=search_filters, top_k=top_k * 2  # 檢索更多候選，後續重排
        )

        # 4. 重排序優化（如果啟用）
        if enable_reranking and len(initial_results) > top_k:
            final_results = await self._rerank_results(
                query, initial_results, query_analysis, top_k
            )
        else:
            final_results = initial_results[:top_k]

        return final_results, query_analysis

    async def _analyze_query(self, query: str) -> QueryAnalysis:
        """分析用戶查詢的意圖和實體"""

        analysis_prompt = f"""
分析以下用戶查詢，識別查詢意圖和重要實體：

用戶查詢：{query}

請從以下意圖類別中選擇最符合的：
{', '.join(self.intent_categories)}

請以JSON格式回答：
{{
    "intent": "選擇的意圖類別",
    "entities": {{
        "products": ["識別的產品名稱"],
        "locations": ["識別的地區"],
        "departments": ["相關部門"],
        "time_periods": ["時間相關"],
        "amounts": ["金額相關"]
    }},
    "keywords": ["關鍵詞1", "關鍵詞2", "關鍵詞3"],
    "suggested_filters": {{
        "doc_type": ["建議的文檔類型"],
        "department": ["建議的部門"],
        "product_line": ["建議的產品線"]
    }}
}}
"""

        try:
            response = await self.llm_client.generate_async(
                prompt=analysis_prompt, max_tokens=400, temperature=0.2
            )

            result = json.loads(response.strip())

            return QueryAnalysis(
                intent=result.get("intent", "一般問答"),
                entities=result.get("entities", {}),
                keywords=result.get("keywords", []),
                filters=result.get("suggested_filters", {}),
            )

        except Exception as e:
            print(f"Query analysis failed: {e}")
            # 返回基礎分析
            return QueryAnalysis(
                intent="一般問答", entities={}, keywords=query.split()[:5], filters={}
            )

    def _build_search_filters(self, analysis: QueryAnalysis) -> Dict:
        """根據查詢分析構建Qdrant檢索過濾條件"""

        filters = {"must": []}

        # 根據意圖設定文檔類型過濾
        if analysis.intent == "價格查詢":
            filters["must"].append(
                {"key": "doc_type", "match": {"any": ["價格", "產品手冊"]}}
            )
        elif analysis.intent == "故障排除":
            filters["must"].append(
                {"key": "doc_type", "match": {"any": ["FAQ", "技術手冊"]}}
            )
        elif analysis.intent == "政策說明":
            filters["must"].append(
                {"key": "doc_type", "match": {"any": ["政策", "規範"]}}
            )

        # 根據實體設定過濾條件
        entities = analysis.entities

        if entities.get("products"):
            # 產品相關過濾
            filters["must"].append(
                {"key": "tags", "match": {"any": entities["products"]}}
            )

        if entities.get("departments"):
            filters["must"].append(
                {"key": "department", "match": {"any": entities["departments"]}}
            )

        # 如果沒有特定過濾條件，使用建議的過濾
        if not filters["must"] and analysis.filters:
            for key, values in analysis.filters.items():
                if values:
                    filters["must"].append({"key": key, "match": {"any": values}})

        return filters if filters["must"] else None

    async def _vector_search(
        self, query: str, filters: Optional[Dict] = None, top_k: int = 10
    ) -> List[SearchResult]:
        """執行向量檢索"""

        try:
            # 使用vectorstore服務執行檢索
            results = await self.vectorstore.search_async(
                query_text=query, top_k=top_k, filters=filters
            )

            search_results = []
            for result in results:
                search_results.append(
                    SearchResult(
                        content=result.get("content", ""),
                        score=result.get("score", 0.0),
                        metadata=result.get("metadata", {}),
                        chunk_id=result.get("id", ""),
                        document_id=result.get("metadata", {}).get("document_id", ""),
                    )
                )

            return search_results

        except Exception as e:
            print(f"Vector search failed: {e}")
            return []

    async def _rerank_results(
        self,
        query: str,
        results: List[SearchResult],
        analysis: QueryAnalysis,
        top_k: int,
    ) -> List[SearchResult]:
        """使用LLM重排序檢索結果"""

        # 準備重排序的內容
        candidates = []
        for i, result in enumerate(results):
            candidates.append(
                {
                    "index": i,
                    "content": result.content[:300],  # 限制長度
                    "metadata": {
                        "doc_type": result.metadata.get("doc_type", ""),
                        "department": result.metadata.get("department", ""),
                        "tags": result.metadata.get("tags", [])[:3],  # 只取前3個標籤
                    },
                }
            )

        rerank_prompt = f"""
用戶查詢：{query}
查詢意圖：{analysis.intent}

請根據與用戶查詢的相關性，對以下候選結果進行重新排序。
考慮因素：
1. 內容與查詢的語意相關性
2. 文檔類型的匹配度
3. 標籤的相關性

候選結果：
{json.dumps(candidates, ensure_ascii=False, indent=2)[:2000]}

請返回重排序後的索引列表，按相關性從高到低排序：
[最相關的索引, 第二相關的索引, ...]

只返回數字陣列，取前{top_k}個：
"""

        try:
            response = await self.llm_client.generate_async(
                prompt=rerank_prompt, max_tokens=100, temperature=0.1
            )

            # 解析重排序結果
            reranked_indices = json.loads(response.strip())

            # 根據重排序結果重新組織
            reranked_results = []
            for idx in reranked_indices:
                if 0 <= idx < len(results):
                    reranked_results.append(results[idx])
                if len(reranked_results) >= top_k:
                    break

            return reranked_results

        except Exception as e:
            print(f"Reranking failed: {e}")
            # 重排序失敗時返回原始結果
            return results[:top_k]

    async def multi_document_search(
        self, query: str, max_documents: int = 5
    ) -> List[Dict]:
        """
        多文檔整合搜尋
        從不同文檔中檢索相關信息並整合
        """

        # 執行增強檢索
        search_results, analysis = await self.enhanced_search(
            query, top_k=max_documents * 3
        )

        # 按文檔分組
        doc_groups = {}
        for result in search_results:
            doc_id = result.document_id
            if doc_id not in doc_groups:
                doc_groups[doc_id] = []
            doc_groups[doc_id].append(result)

        # 選擇最相關的文檔
        integrated_results = []
        for doc_id, chunks in list(doc_groups.items())[:max_documents]:
            # 取每個文檔最相關的chunk
            best_chunk = max(chunks, key=lambda x: x.score)

            integrated_results.append(
                {
                    "document_id": doc_id,
                    "content": best_chunk.content,
                    "metadata": best_chunk.metadata,
                    "score": best_chunk.score,
                    "total_chunks": len(chunks),
                }
            )

        return integrated_results


# 全域服務實例
enhanced_search_service = EnhancedSearchService()


def get_enhanced_search_service() -> EnhancedSearchService:
    """取得增強檢索服務實例"""
    return enhanced_search_service
