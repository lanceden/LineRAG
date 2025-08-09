from __future__ import annotations
from typing import List
from langchain.schema import Document

from app.schemas.ask import Message
from app.services.llm import get_llm_client
from app.services.vectorstore import get_vectorstore_service


def build_prompt(messages: List[Message], max_rounds: int = 3) -> str:
    selected = messages[-max_rounds * 2 :]
    prompt = ""
    for msg in selected:
        role = msg.role
        content = msg.parts[0]["text"] if msg.parts and "text" in msg.parts[0] else ""
        prefix = "使用者：" if role == "user" else "系統："
        prompt += f"{prefix}{content}\n"
    return prompt


def build_rag_prompt(question: str, documents: List[Document]) -> str:
    context = "\n\n".join([
        f"[第 {doc.metadata.get('page_number', '?')} 頁]\n{doc.page_content}" for doc in documents
    ])
    prompt = f"""你是一位親切且專業的健身客服助理，請用溫暖、鼓勵的語氣回覆用戶，只可以回答與健身相關的問題。

文件內容如下：
---
{context}
---

問題：{question}
請以繁體中文簡潔、友善地作答。範例：「您好，很高興為您解答！...祝您順心如意！」
"""
    return prompt


def generate_answer_from_messages(messages: List[Message]) -> str:
    vs = get_vectorstore_service()
    llm = get_llm_client()

    question = build_prompt(messages)

    # if no vectorstore ready, return graceful message
    if not vs.is_ready():
        return f"您好，很抱歉系統暫時無法查詢相關資料。\n\n問題：{question}\n請稍後再試，或聯繫客服人員協助。謝謝您的耐心！"

    try:
        docs: List[Document] = vs.retriever.get_relevant_documents(question)
        rag_prompt = build_rag_prompt(question, docs)
        answer = llm.chat([
            {"role": "system", "content": "你是一位親切且專業的健身客服助理，請用溫暖、鼓勵的語氣回覆用戶，只可以回答與健身相關的問題。"},
            {"role": "user", "content": rag_prompt},
        ])
        return answer
    except Exception:
        # hide internals, return user-friendly message
        return f"您好，很抱歉在查詢相關資料時遇到問題。\n\n問題：{question}\n請稍後再試，或聯繫客服人員協助。謝謝您的理解！"
