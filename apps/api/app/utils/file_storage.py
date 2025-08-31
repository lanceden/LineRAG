import os
import uuid
from pathlib import Path
from typing import Tuple

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
}


def validate_extension(filename: str):
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不支援的文件格式: {ext}")
    return ext


def generate_doc_id_and_unique_name(original_filename: str) -> Tuple[str, str]:
    doc_id = str(uuid.uuid4())
    ext = Path(original_filename).suffix
    return doc_id, f"{doc_id}{ext}"  # unique stored name


def write_file_bytes(target_dir: Path, unique_filename: str, content: bytes) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    abs_path = (target_dir / unique_filename).absolute()
    with open(abs_path, "wb") as f:
        f.write(content)
    if not abs_path.exists():
        raise IOError("文件寫入後不存在")
    if abs_path.stat().st_size != len(content):
        raise IOError("文件大小驗證失敗")
    return abs_path
