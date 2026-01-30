# transcriber_app/api/models.py
from pydantic import BaseModel
from typing import List, Literal

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    transcripcion: str
    resumen: str
    pregunta: str
    historial: List[ChatMessage] = []

