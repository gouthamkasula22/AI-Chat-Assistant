from pydantic import BaseModel
from typing import List, Dict

class ChatRequest(BaseModel):
    history: List[Dict[str, str]]

class ChatResponse(BaseModel):
    reply: str