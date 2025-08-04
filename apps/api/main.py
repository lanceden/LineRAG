from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import requests
import json
from pydantic import BaseModel
from typing import Dict, List, Literal, Optional


class MessagePart(BaseModel):
    type: Literal["text"]
    text: str


class Message(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    parts: List[Dict[str, str]]


class AskRequest(BaseModel):
    messages: List[Message]
    trigger: Optional[str] = None


app = FastAPI()

# ⬇️ 載入向量資料庫
embedding = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3", encode_kwargs={"normalize_embeddings": True}
)

vectordb = FAISS.load_local(
    "./vectorstore", embeddings=embedding, allow_dangerous_deserialization=True
)
retriever = vectordb.as_retriever()


# ⬇️ 定義資料結構
class AskInput(BaseModel):
    question: str
    userId: str


# 組合最後幾輪對話（保留 user/assistant）
def build_prompt(messages: List[Message], max_rounds: int = 3) -> str:
    selected = messages[-max_rounds * 2 :]  # 每輪有 user+assistant
    prompt = ""
    for msg in selected:
        role = msg.role
        content = msg.parts[0]["text"]
        prefix = "使用者：" if role == "user" else "系統："
        prompt += f"{prefix}{content}\n"
    return prompt


# ⬇️ 呼叫 Ollama 的本地 API
def call_ollama_stream(prompt: str):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma3n:e2b",  # 依你裝的模型修改（如 qwen:3b、llama3、gemma 等）
            "prompt": prompt,
            "stream": True,
        },
        stream=True,
    )
    # 逐行解析 Ollama 回應並轉換成前端期望的格式

    for line in response.iter_lines():
        if line:
            try:
                # 解析 Ollama 的 JSON 回應
                ollama_data = json.loads(line.decode("utf-8"))
                if "response" in ollama_data and ollama_data["response"]:
                    # 轉換成前端期望的格式
                    frontend_data = {"type": "text", "text": ollama_data["response"]}
                    yield f"data: {json.dumps(frontend_data)}\n\n"

                # 檢查是否完成
                if ollama_data.get("done", False):
                    break
            except json.JSONDecodeError:
                # 忽略無效的 JSON 行
                continue

    yield "data: [DONE]\n\n"


# ⬇️ QA Chain: 建 prompt + 丟給 Ollama
def qa_chain(question: str) -> str:
    docs: list[Document] = retriever.get_relevant_documents(question)
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""你是一位親切且專業的健身客服助理，請用溫暖、鼓勵的語氣回覆用戶，只可以回答與健身相關的問題。

文件內容如下：
---
{context}
---

問題：{question}

請以繁體中文簡潔、友善地作答。
範例：「您好，很高興為您解答！...祝您順心如意！」"""

    return prompt


# ⬇️ FastAPI Endpoint
@app.post("/ask")
@app.post("/ask")
def ask(input: AskRequest):
    prompt = build_prompt(input.messages)
    qa_prompt = qa_chain(prompt)
    return StreamingResponse(
        call_ollama_stream(qa_prompt), media_type="text/event-stream"
    )
