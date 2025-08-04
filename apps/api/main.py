from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import requests
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
def call_ollama(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma3n:e2b",  # 依你裝的模型修改（如 qwen:3b、llama3、gemma 等）
            "prompt": prompt,
            "stream": False,
        },
    )
    return response.json()["response"]


# ⬇️ QA Chain: 建 prompt + 丟給 Ollama
def qa_chain(question: str) -> str:
    docs: list[Document] = retriever.get_relevant_documents(question)
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""你是一位親切且專業的客服助理，請用溫暖、鼓勵的語氣回覆用戶，並在回答最後加上一句祝福或鼓勵的話。

文件內容如下：
---
{context}
---

問題：{question}

請以繁體中文簡潔、友善地作答。
範例：「您好，很高興為您解答！...祝您順心如意！」"""

    return call_ollama(prompt)


# ⬇️ FastAPI Endpoint
@app.post("/ask")
def ask(input: AskRequest):
    prompt = build_prompt(input.messages)
    answer = qa_chain(prompt)
    return {"answer": answer}
