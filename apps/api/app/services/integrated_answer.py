"""
多文檔整合回答生成服務
實現方案A的核心功能：整合多個文檔片段生成完整、準確的回答
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass

from app.services.llm import get_llm_client
from app.services.enhanced_search import get_enhanced_search_service, SearchResult


@dataclass
class IntegratedAnswer:
    """整合回答結果"""

    answer: str
    confidence: float
    sources: List[Dict]
    answer_type: str  # 完整回答、部分回答、無法回答
    suggestions: List[str]  # 相關建議


class IntegratedAnswerService:
    """多文檔整合回答服務"""

    def __init__(self):
        self.llm_client = get_llm_client()
        self.search_service = get_enhanced_search_service()

    async def generate_integrated_answer(
        self, query: str, max_sources: int = 5, min_confidence: float = 0.3
    ) -> IntegratedAnswer:
        """
        生成整合多個文檔的完整回答

        Args:
            query: 用戶問題
            max_sources: 最大參考來源數
            min_confidence: 最小信心度閾值

        Returns:
            整合回答結果
        """

        # 1. 執行多文檔檢索
        search_results = await self.search_service.multi_document_search(
            query, max_documents=max_sources
        )

        if not search_results:
            return IntegratedAnswer(
                answer="抱歉，我找不到相關資訊來回答您的問題。請嘗試使用不同的關鍵詞或聯繫客服人員。",
                confidence=0.0,
                sources=[],
                answer_type="無法回答",
                suggestions=["聯繫客服", "查看常見問題", "嘗試其他關鍵詞"],
            )

        # 2. 過濾低信心度結果
        filtered_results = [
            result for result in search_results if result["score"] >= min_confidence
        ]

        if not filtered_results:
            return await self._generate_low_confidence_answer(query, search_results)

        # 3. 生成整合回答
        return await self._generate_comprehensive_answer(query, filtered_results)

    async def _generate_comprehensive_answer(
        self, query: str, search_results: List[Dict]
    ) -> IntegratedAnswer:
        """生成完整的整合回答"""

        # 準備參考資料
        sources_text = ""
        source_info = []

        for i, result in enumerate(search_results, 1):
            metadata = result["metadata"]
            sources_text += f"\n【資料來源 {i}】\n"
            sources_text += f"文檔類型：{metadata.get('doc_type', '未知')}\n"
            sources_text += f"部門：{metadata.get('department', '未知')}\n"
            sources_text += f"內容：{result['content']}\n"

            source_info.append(
                {
                    "index": i,
                    "document_id": result["document_id"],
                    "doc_type": metadata.get("doc_type", "未知"),
                    "department": metadata.get("department", "未知"),
                    "score": result["score"],
                    "snippet": result["content"][:100] + "...",
                }
            )

        # 生成整合回答
        integration_prompt = f"""
請基於以下多個參考資料，為用戶問題提供完整、準確的回答。

用戶問題：{query}

參考資料：{sources_text}

回答要求：
1. 整合所有相關信息，提供完整答案
2. 如果不同資料來源有差異，請分別說明
3. 標注信息來源（使用【資料來源X】）
4. 使用清晰的結構和格式
5. 如果信息不完整，明確說明並建議後續動作

請以以下JSON格式回答：
{{
    "answer": "完整的回答內容",
    "confidence": 0.85,
    "answer_type": "完整回答",
    "key_points": ["重點1", "重點2", "重點3"],
    "sources_used": [1, 2, 3],
    "suggestions": ["建議1", "建議2"]
}}
"""

        try:
            response = await self.llm_client.generate_async(
                prompt=integration_prompt, max_tokens=800, temperature=0.3
            )

            result = json.loads(response.strip())

            return IntegratedAnswer(
                answer=result.get("answer", ""),
                confidence=result.get("confidence", 0.7),
                sources=source_info,
                answer_type=result.get("answer_type", "完整回答"),
                suggestions=result.get("suggestions", []),
            )

        except Exception as e:
            print(f"Integration failed: {e}")
            return await self._generate_fallback_answer(query, search_results)

    async def _generate_low_confidence_answer(
        self, query: str, search_results: List[Dict]
    ) -> IntegratedAnswer:
        """處理低信心度的情況"""

        # 嘗試提供部分相關信息
        if search_results:
            best_result = max(search_results, key=lambda x: x["score"])

            fallback_prompt = f"""
用戶問題：{query}

雖然我找到一些可能相關的資訊，但匹配度不高：

{best_result["content"][:400]}

請提供一個誠實的回答：
1. 說明找到的資訊可能相關但不確定
2. 提供找到的部分信息
3. 建議用戶如何獲得更準確的答案

以JSON格式回答：
{{
    "answer": "部分回答內容",
    "confidence": 0.4,
    "suggestions": ["建議1", "建議2"]
}}
"""

            try:
                response = await self.llm_client.generate_async(
                    prompt=fallback_prompt, max_tokens=400, temperature=0.4
                )

                result = json.loads(response.strip())

                return IntegratedAnswer(
                    answer=result.get("answer", ""),
                    confidence=result.get("confidence", 0.4),
                    sources=[
                        {
                            "index": 1,
                            "document_id": best_result["document_id"],
                            "score": best_result["score"],
                            "snippet": best_result["content"][:100] + "...",
                        }
                    ],
                    answer_type="部分回答",
                    suggestions=result.get("suggestions", []),
                )

            except Exception as e:
                print(f"Fallback answer generation failed: {e}")

        return IntegratedAnswer(
            answer="很抱歉，我找不到足夠相關的資訊來回答您的問題。建議您：\n1. 使用不同的關鍵詞重新提問\n2. 聯繫客服人員獲得協助\n3. 查看相關的常見問題",
            confidence=0.2,
            sources=[],
            answer_type="無法回答",
            suggestions=["重新提問", "聯繫客服", "查看FAQ"],
        )

    async def _generate_fallback_answer(
        self, query: str, search_results: List[Dict]
    ) -> IntegratedAnswer:
        """生成備案回答（當JSON解析失敗時）"""

        # 簡單整合最相關的幾個結果
        top_results = search_results[:3]
        combined_content = "\n\n".join([r["content"][:200] for r in top_results])

        simple_prompt = f"""
基於以下資料回答用戶問題：

問題：{query}

資料：
{combined_content}

請提供簡潔明確的回答：
"""

        try:
            answer = await self.llm_client.generate_async(
                prompt=simple_prompt, max_tokens=400, temperature=0.3
            )

            return IntegratedAnswer(
                answer=answer.strip(),
                confidence=0.6,
                sources=[
                    {
                        "index": i + 1,
                        "document_id": result["document_id"],
                        "score": result["score"],
                        "snippet": result["content"][:100] + "...",
                    }
                    for i, result in enumerate(top_results)
                ],
                answer_type="基礎回答",
                suggestions=["如需更詳細信息，請聯繫客服"],
            )

        except Exception as e:
            print(f"Simple answer generation failed: {e}")
            return IntegratedAnswer(
                answer="系統暫時無法處理您的問題，請稍後再試或聯繫客服人員。",
                confidence=0.1,
                sources=[],
                answer_type="系統錯誤",
                suggestions=["稍後重試", "聯繫客服"],
            )

    async def generate_conversational_answer(
        self, query: str, context: List[Dict], max_context: int = 3
    ) -> IntegratedAnswer:
        """
        生成考慮對話上下文的回答

        Args:
            query: 當前問題
            context: 對話歷史上下文
            max_context: 最大上下文輪數

        Returns:
            整合回答結果
        """

        # 分析是否需要上下文
        context_needed = await self._analyze_context_dependency(
            query, context[-max_context:]
        )

        if context_needed and context:
            # 重寫查詢以包含上下文信息
            enhanced_query = await self._enhance_query_with_context(
                query, context[-max_context:]
            )
            return await self.generate_integrated_answer(enhanced_query)
        else:
            # 直接回答當前問題
            return await self.generate_integrated_answer(query)

    async def _analyze_context_dependency(
        self, query: str, context: List[Dict]
    ) -> bool:
        """分析查詢是否依賴上下文"""

        # 檢查是否包含指示詞
        context_indicators = [
            "它",
            "這個",
            "那個",
            "剛才",
            "上面",
            "繼續",
            "還有",
            "另外",
        ]

        query_lower = query.lower()
        for indicator in context_indicators:
            if indicator in query_lower:
                return True

        return False

    async def _enhance_query_with_context(self, query: str, context: List[Dict]) -> str:
        """使用上下文增強查詢"""

        context_text = ""
        for turn in context:
            context_text += f"用戶：{turn.get('user_message', '')}\n"
            context_text += f"助手：{turn.get('assistant_message', '')}\n\n"

        enhancement_prompt = f"""
基於對話上下文，重寫用戶的當前問題，使其更完整和明確。

對話上下文：
{context_text}

當前問題：{query}

重寫後的完整問題：
"""

        try:
            enhanced = await self.llm_client.generate_async(
                prompt=enhancement_prompt, max_tokens=200, temperature=0.3
            )
            return enhanced.strip()
        except Exception:
            return query


# 全域服務實例
integrated_answer_service = IntegratedAnswerService()


def get_integrated_answer_service() -> IntegratedAnswerService:
    """取得多文檔整合回答服務實例"""
    return integrated_answer_service
