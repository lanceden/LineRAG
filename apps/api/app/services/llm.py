from __future__ import annotations
import os
from typing import List, Dict
from openai import OpenAI

# Load .env
from app.core import env


class LlmClient:
    def __init__(self, api_base: str | None = None, api_key: str | None = None, model_name: str | None = None):
        self.api_base = api_base or os.getenv("OPENAI_API_BASE", "http://localhost:8001/v1")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "not-needed")
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "opt-1.3b")
        
        # 使用新版OpenAI client
        self.client = OpenAI(
            base_url=self.api_base,
            api_key=self.api_key
        )

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
        )
        # vLLM 的 message.content 可能返回 None，嘗試不同方式獲取內容
        message = resp.choices[0].message
        if message.content is not None:
            return message.content
        
        # 如果 content 是 None，嘗試從 message 的字典表示中獲取
        if hasattr(message, 'model_dump'):
            message_dict = message.model_dump()
            return message_dict.get('content', '')
        
        return ""


llm_client = LlmClient()

def get_llm_client() -> LlmClient:
    return llm_client
