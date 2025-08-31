from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal


class MultimodalContentItem(BaseModel):
    """多模態內容項目"""

    type: Literal["text", "image", "table", "equation"]
    # 文本內容
    text: Optional[str] = None
    # 圖像內容
    img_path: Optional[str] = None
    img_caption: Optional[List[str]] = None
    img_footnote: Optional[List[str]] = None
    # 表格內容
    table_body: Optional[str] = None
    table_caption: Optional[List[str]] = None
    table_footnote: Optional[List[str]] = None
    # 公式內容
    latex: Optional[str] = None
    # 頁碼
    page_idx: Optional[int] = 0


class IngestRequest(BaseModel):
    """文檔擷取請求"""

    file_path: str
    company_id: int
    user_id: int
    content_list: Optional[List[MultimodalContentItem]] = None
    use_ocr: Optional[bool] = False


class IngestResponse(BaseModel):
    """文檔擷取回應"""

    success: bool
    message: str
    document_id: Optional[str] = None
    task_id: Optional[str] = None
