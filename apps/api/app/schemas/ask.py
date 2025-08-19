from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel


class MessagePart(BaseModel):
    type: Literal["text", "image"]
    text: Optional[str] = None
    image_url: Optional[str] = None


class Message(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str  # 簡化為字符串內容
    parts: Optional[List[Dict[str, str]]] = None  # 保持向後兼容


class AskRequest(BaseModel):
    messages: List[Message]
    company_id: int  # 必須提供公司 ID
    trigger: Optional[str] = None


class MultimodalContent(BaseModel):
    """多模態內容結構"""

    type: Literal["image", "table", "equation"]
    # 圖像內容
    img_path: Optional[str] = None
    img_caption: Optional[List[str]] = None
    img_footnote: Optional[List[str]] = None
    # 表格內容
    table_data: Optional[str] = None
    table_caption: Optional[str] = None
    # 公式內容
    latex: Optional[str] = None
    equation_caption: Optional[str] = None


class MultimodalAskRequest(BaseModel):
    """支援多模態內容的詢問請求"""

    messages: List[Message]
    multimodal_content: List[MultimodalContent]
    company_id: int  # 必須提供公司 ID
    trigger: Optional[str] = None
