import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv

from app.schemas.image import ImageQuestionRequest

load_dotenv()

# 定義 API 路由，前綴為空，標籤為 "image"
router = APIRouter(prefix="", tags=["image"])


@router.post("/ask-image")
def ask_image(request: ImageQuestionRequest):
    """
    處理圖像問題請求。
    接收包含圖片路徑和問題的 ImageQuestionRequest 物件，
    調用 multimodal_service 的 analyze_equipment_image 方法來分析圖片並回答問題。
    如果圖片不存在，則拋出 404 錯誤。
    """
    # 直接沿用既有 multimodal_service 的行為
    from app.services.multimodal_service import get_multimodal_service

    if not os.path.exists(request.image_path):
        raise HTTPException(status_code=404, detail="圖片文件不存在")

    ms = get_multimodal_service()
    answer = ms.analyze_equipment_image(request.image_path, request.question)
    return {"text": answer}


@router.post("/ocr-extract")
def ocr_extract(request: ImageQuestionRequest):
    """
    從圖像中提取文字。
    接收包含圖片路徑的 ImageQuestionRequest 物件，
    調用 multimodal_service 的 extract_text_from_image 方法來提取文字。
    如果圖片不存在，則拋出 404 錯誤。
    """
    from app.services.multimodal_service import get_multimodal_service

    if not os.path.exists(request.image_path):
        raise HTTPException(status_code=404, detail="圖片文件不存在")

    ms = get_multimodal_service()
    extracted_text = ms.extract_text_from_image(request.image_path)
    return {"text": extracted_text, "file_path": request.image_path}


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """
    上傳圖片文件。
    驗證上傳的文件是否為圖片格式，
    為文件生成一個唯一的檔案名稱，
    並將文件儲存到指定的上傳目錄中。
    返回上傳成功訊息、檔案路徑和原始檔名。
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只支援圖片文件")

    upload_dir = os.getenv("UPLOAD_IMAGE_DIR", "./uploads/images")
    os.makedirs(upload_dir, exist_ok=True)

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {
        "message": "圖片上傳成功",
        "file_path": file_path,
        "original_name": file.filename,
    }
