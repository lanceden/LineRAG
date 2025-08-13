"""
Admin API routes
"""
from fastapi import APIRouter
import time
import httpx
import os

router = APIRouter(prefix="/admin", tags=["管理"])

# 全域狀態存儲
model_state = {
    "currentModel": "Qwen2-1.5B-Instruct",
    "status": "running",
    "lastCheckTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}

async def get_vllm_model_info():
    """從vLLM獲取模型資訊並添加描述"""
    try:
        vllm_url = os.getenv("OPENAI_API_BASE", "http://localhost:8001")
        if vllm_url.endswith("/v1"):
            vllm_url = vllm_url[:-3]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{vllm_url}/v1/models")
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    model_data = data["data"][0]
                    model_id = model_data["id"]
                    
                    # 根據模型ID添加描述資訊
                    model_info = {
                        "id": model_id,
                        "name": model_id,
                        "displayName": model_id,
                        "description": "當前運行的模型",
                        "vramUsage": "未知",
                        "capabilities": ["文字對話"]
                    }
                    
                    # 根據模型名稱自動判斷特性
                    if "1.5B" in model_id:
                        model_info.update({
                            "description": "輕量級模型，適合測試",
                            "vramUsage": "~3GB",
                            "capabilities": ["文字對話", "指令跟隨"]
                        })
                    elif "VL" in model_id:
                        model_info.update({
                            "description": "支援圖文混合對話",
                            "vramUsage": "~16GB", 
                            "capabilities": ["文字對話", "圖片識別", "多模態"]
                        })
                    elif "Chat" in model_id:
                        model_info.update({
                            "description": "純文字對話，效能優異",
                            "vramUsage": "~14GB",
                            "capabilities": ["文字對話", "中文優化"]
                        })
                    
                    return model_info
                    
    except Exception as e:
        print(f"Error getting vLLM model: {e}")
    
    # 返回預設模型資訊
    return {
        "id": model_state["currentModel"],
        "name": model_state["currentModel"],
        "displayName": model_state["currentModel"],
        "description": "當前運行的模型",
        "vramUsage": "未知",
        "capabilities": ["文字對話"]
    }

@router.get("/model/status")
async def get_model_status():
    """獲取模型狀態和詳細資訊"""
    # 從vLLM獲取模型資訊
    model_info = await get_vllm_model_info()
    
    # 更新最後檢查時間為當前時間
    model_state["lastCheckTime"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    model_state["currentModel"] = model_info["id"]
    
    # 返回狀態和模型詳細資訊
    return {
        **model_state,
        "modelInfo": model_info
    }

