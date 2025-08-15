from fastapi import FastAPI, HTTPException
from models.chat_models import ChatRequest, ChatResponse
from controllers.chat_controller import get_llm_reply

app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        reply = get_llm_reply(request.history)
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))