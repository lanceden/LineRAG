from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import requests
from pydantic import BaseModel
from typing import List, Literal


class MessagePart(BaseModel):
    type: Literal["text"]
    text: str


class Message(BaseModel):
    id: str
    role: Literal["user"]
    parts: List[MessagePart]


class AskRequest(BaseModel):
    messages: List[Message]
    trigger: str


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


# ⬇️ 呼叫 Ollama 的本地 API
def call_ollama(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3:8b",  # 依你裝的模型修改（如 qwen:3b、llama3、gemma 等）
            "prompt": prompt,
            "stream": False,
        },
    )
    return response.json()["response"]


# ⬇️ QA Chain: 建 prompt + 丟給 Ollama
def qa_chain(question: str) -> str:
    docs: list[Document] = retriever.get_relevant_documents(question)
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""你是一位客服助理，請根據以下資料回答用戶問題，若找不到資訊則回答「文件中未提及」。

文件內容如下：
---
{context}
---

問題：{question}

請以繁體中文簡潔作答。"""

    return call_ollama(prompt)


# ⬇️ FastAPI Endpoint
@app.post("/ask")
def ask(input: AskRequest):
    last_message = input.messages[-1].parts[0].text  # 取最新訊息內容
    answer = qa_chain(last_message)
    return {"answer": answer}
