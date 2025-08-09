from pydantic import BaseModel
from typing import Optional


class IngestRequest(BaseModel):
    file_path: str
    original_name: str
    use_ocr: Optional[bool] = False
