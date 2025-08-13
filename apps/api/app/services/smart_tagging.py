"""
智能標籤提取與文檔分類服務
實現方案A的核心功能：自動分類演算法與標籤提取
"""

import re
import json
from typing import Dict, List, Optional
from datetime import datetime

from app.services.llm import get_llm_client


class SmartTaggingService:
    """智能標籤提取與文檔自動分類"""

    def __init__(self):
        self.llm_client = get_llm_client()

        # 預定義分類體系
        self.classification_schema = {
            "department": ["客服", "產品", "技術", "法務", "財務", "人事", "通用"],
            "doc_type": ["FAQ", "政策", "手冊", "價格", "流程", "公告", "規範"],
            "product_line": ["產品A", "產品B", "產品C", "通用服務", "其他"],
            "priority": ["高", "中", "低"],
            "audience": ["客戶", "員工", "合作夥伴", "公開"],
        }

    async def analyze_document(self, content: str, filename: str = "") -> Dict:
        """
        分析文檔內容，提取分類和標籤

        Args:
            content: 文檔內容
            filename: 檔案名稱

        Returns:
            分析結果包含分類、標籤、摘要等
        """

        # 1. 自動分類
        classification = await self._classify_document(content, filename)

        # 2. 提取智能標籤
        tags = await self._extract_smart_tags(content)

        # 3. 生成文檔摘要
        summary = await self._generate_summary(content)

        # 4. 提取關鍵實體
        entities = await self._extract_entities(content)

        return {
            "classification": classification,
            "tags": tags,
            "summary": summary,
            "entities": entities,
            "processed_at": datetime.now().isoformat(),
            "content_length": len(content),
            "filename": filename,
        }

    async def _classify_document(self, content: str, filename: str) -> Dict:
        """使用LLM進行文檔自動分類"""

        classification_prompt = f"""
請分析以下文檔內容，並根據分類體系進行自動分類。

檔案名稱：{filename}
文檔內容（前500字）：
{content[:500]}

請從以下選項中選擇最適合的分類：

部門分類：{', '.join(self.classification_schema['department'])}
文檔類型：{', '.join(self.classification_schema['doc_type'])}
產品線：{', '.join(self.classification_schema['product_line'])}
重要程度：{', '.join(self.classification_schema['priority'])}
適用對象：{', '.join(self.classification_schema['audience'])}

請以JSON格式回答：
{{
    "department": "選擇的部門",
    "doc_type": "選擇的類型",
    "product_line": "選擇的產品線",
    "priority": "選擇的重要程度",
    "audience": "選擇的對象",
    "confidence": 0.85,
    "reasoning": "分類理由"
}}
"""

        try:
            response = await self.llm_client.generate_async(
                prompt=classification_prompt, max_tokens=300, temperature=0.3
            )

            # 嘗試解析JSON回應
            result = json.loads(response.strip())
            return result

        except Exception as e:
            print(f"Classification failed: {e}")
            # 返回預設分類
            return {
                "department": "通用",
                "doc_type": "其他",
                "product_line": "通用服務",
                "priority": "中",
                "audience": "員工",
                "confidence": 0.5,
                "reasoning": "自動分類失敗，使用預設值",
            }

    async def _extract_smart_tags(self, content: str) -> List[str]:
        """提取智能標籤"""

        tagging_prompt = f"""
分析以下文檔內容，提取10-15個最重要的標籤關鍵字。

標籤應該包括：
1. 核心概念和主題
2. 產品名稱和功能
3. 業務流程和術語
4. 重要的實體和概念

文檔內容：
{content[:800]}

請以JSON陣列格式回答，例如：
["客戶服務", "退換貨政策", "品質保證", "聯絡方式", "處理時間"]

只返回標籤陣列，不要其他文字：
"""

        try:
            response = await self.llm_client.generate_async(
                prompt=tagging_prompt, max_tokens=200, temperature=0.4
            )

            # 解析標籤
            tags = json.loads(response.strip())

            # 清理和驗證標籤
            clean_tags = []
            for tag in tags:
                if isinstance(tag, str) and len(tag.strip()) > 1:
                    clean_tags.append(tag.strip())

            return clean_tags[:15]  # 限制最多15個標籤

        except Exception as e:
            print(f"Tag extraction failed: {e}")
            # 使用規則式方法作為備案
            return self._extract_tags_by_rules(content)

    def _extract_tags_by_rules(self, content: str) -> List[str]:
        """使用規則式方法提取標籤（備案方法）"""

        # 常見的業務關鍵字
        business_keywords = [
            "客服",
            "產品",
            "價格",
            "保固",
            "退換貨",
            "付款",
            "運送",
            "會員",
            "註冊",
            "登入",
            "帳戶",
            "訂單",
            "購買",
            "折扣",
            "技術支援",
            "故障",
            "維修",
            "更新",
            "安裝",
            "設定",
        ]

        found_tags = []
        content_lower = content.lower()

        for keyword in business_keywords:
            if keyword in content_lower:
                found_tags.append(keyword)

        # 使用正則提取可能的產品名稱（大寫開頭的詞組）
        product_pattern = r"\b[A-Z][A-Za-z0-9\-_]{2,15}\b"
        products = re.findall(product_pattern, content)
        found_tags.extend(products[:5])

        return list(set(found_tags))[:10]

    async def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成文檔摘要"""

        summary_prompt = f"""
請為以下文檔內容生成一個簡潔的摘要，長度控制在{max_length}字以內。

摘要應該：
1. 概括文檔主要內容和目的
2. 突出重要信息和關鍵點
3. 使用簡潔清晰的語言

文檔內容：
{content[:1000]}

摘要：
"""

        try:
            summary = await self.llm_client.generate_async(
                prompt=summary_prompt, max_tokens=max_length, temperature=0.3
            )

            return summary.strip()

        except Exception as e:
            print(f"Summary generation failed: {e}")
            # 簡單的摘要備案
            sentences = content[:500].split("。")
            return sentences[0][:max_length] + "..."

    async def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """提取命名實體"""

        entity_prompt = f"""
從以下文檔內容中提取重要的實體信息：

文檔內容：
{content[:600]}

請識別並分類提取以下類型的實體：
- 產品名稱
- 公司/部門名稱  
- 人名/職位
- 地點/地區
- 日期/時間
- 金額/價格
- 聯絡方式

以JSON格式回答：
{{
    "products": ["產品1", "產品2"],
    "organizations": ["公司A", "部門B"],
    "persons": ["張經理", "客服人員"],
    "locations": ["台北", "全台"],
    "dates": ["2024年", "每週一"],
    "amounts": ["NT$1000", "30天"],
    "contacts": ["02-1234-5678", "service@example.com"]
}}
"""

        try:
            response = await self.llm_client.generate_async(
                prompt=entity_prompt, max_tokens=400, temperature=0.2
            )

            entities = json.loads(response.strip())
            return entities

        except Exception as e:
            print(f"Entity extraction failed: {e}")
            return {
                "products": [],
                "organizations": [],
                "persons": [],
                "locations": [],
                "dates": [],
                "amounts": [],
                "contacts": [],
            }


# 全域服務實例
smart_tagging_service = SmartTaggingService()


def get_smart_tagging_service() -> SmartTaggingService:
    """取得智能標籤服務實例"""
    return smart_tagging_service
