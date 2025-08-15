
from fastapi import FastAPI, HTTPException
from models.chat_models import ChatRequest, ChatResponse
from controllers.chat_controller import get_llm_reply

app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Receives a user message and returns a reply from the LLM.
    """
    try:
        reply = get_llm_reply(request.message)
        return ChatResponse(reply=reply)
    except Exception as e:
        # Centralized error handling
        raise HTTPException(status_code=500, detail=str(e))