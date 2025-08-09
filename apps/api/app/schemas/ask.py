from typing import List, Literal, Optional, Dict
from pydantic import BaseModel


class MessagePart(BaseModel):
    type: Literal["text", "image"]
    text: Optional[str] = None
    image_url: Optional[str] = None


class Message(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    parts: List[Dict[str, str]]


class AskRequest(BaseModel):
    messages: List[Message]
    trigger: Optional[str] = None
