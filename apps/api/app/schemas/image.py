from pydantic import BaseModel


class ImageQuestionRequest(BaseModel):
    image_path: str
    question: str
