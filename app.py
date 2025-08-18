"""
FastAPI backend server for the AI Chat Assistant.

This module provides REST API endpoints for chat functionality.
"""

from fastapi import FastAPI, HTTPException

from models.chat_models import ChatRequest, ChatResponse
from controllers.chat_controller import get_llm_reply

app = FastAPI()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Handle chat requests and return AI responses.

    Args:
        request: ChatRequest containing the conversation history

    Returns:
        ChatResponse: The AI assistant's reply

    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        reply = get_llm_reply(request.history)
        return ChatResponse(reply=reply)
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception
