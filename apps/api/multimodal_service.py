"""
多模態推理服務
支援圖片理解、OCR文字識別等功能
"""
from typing import Optional, List, Dict, Any
import base64
import io
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq
import requests
from pathlib import Path

class MultimodalService:
    def __init__(self, model_name: str = "Qwen/Qwen2-VL-2B-Instruct"):
        """
        初始化多模態服務
        
        Args:
            model_name: 使用的多模態模型名稱
        """
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_model(self):
        """載入多模態模型"""
        try:
            print(f"正在載入多模態模型: {self.model_name}")
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            self.model = AutoModelForVision2Seq.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            print(f"✅ 多模態模型載入成功，使用設備: {self.device}")
        except Exception as e:
            print(f"❌ 多模態模型載入失敗: {e}")
            raise
    
    def process_image_with_text(self, image_path: str, prompt: str) -> str:
        """
        處理圖片並回答問題
        
        Args:
            image_path: 圖片路徑
            prompt: 用戶問題
            
        Returns:
            模型回答
        """
        if self.model is None:
            self.load_model()
            
        try:
            # 載入圖片
            image = Image.open(image_path).convert("RGB")
            
            # 構建對話格式
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # 處理輸入
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            
            inputs = self.processor(
                text=[text], 
                images=[image], 
                return_tensors="pt"
            ).to(self.device)
            
            # 生成回答
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                    do_sample=True
                )
            
            # 解碼回答
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in 
                zip(inputs.input_ids, generated_ids)
            ]
            
            response = self.processor.batch_decode(
                generated_ids_trimmed, 
                skip_special_tokens=True, 
                clean_up_tokenization_spaces=False
            )[0]
            
            return response.strip()
            
        except Exception as e:
            print(f"圖片處理失敗: {e}")
            return f"抱歉，處理圖片時發生錯誤: {str(e)}"
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        從圖片中提取文字（OCR功能）
        
        Args:
            image_path: 圖片路徑
            
        Returns:
            提取的文字內容
        """
        ocr_prompt = """請仔細觀察這張圖片，提取其中所有的文字內容。
        要求：
        1. 保持原文的格式和結構
        2. 如果是表格，請保持表格格式
        3. 如果有標題、段落，請保持層次結構
        4. 只輸出文字內容，不要添加任何解釋
        """
        
        return self.process_image_with_text(image_path, ocr_prompt)
    
    def analyze_equipment_image(self, image_path: str, user_question: str) -> str:
        """
        分析器材圖片並回答使用方法
        
        Args:
            image_path: 器材圖片路徑
            user_question: 用戶問題
            
        Returns:
            器材使用說明
        """
        equipment_prompt = f"""你是一位專業的健身教練，請仔細觀察這張器材圖片。

用戶問題：{user_question}

請提供：
1. 器材名稱和類型
2. 主要鍛鍊部位
3. 正確使用方法和步驟
4. 安全注意事項
5. 適合的訓練強度建議

請用親切、專業的語氣回答，確保安全性和實用性。"""

        return self.process_image_with_text(image_path, equipment_prompt)

# 全局多模態服務實例
multimodal_service = MultimodalService()

def get_multimodal_service() -> MultimodalService:
    """獲取多模態服務實例"""
    return multimodal_service