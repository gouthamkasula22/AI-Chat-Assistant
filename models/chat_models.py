"""
Chat API models for request/response data structures.

This module defines the Pydantic models used for API communication
between the frontend and backend services.
"""

from typing import List, Dict
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """
    Request model for chat API endpoint.
    
    Attributes:
        history: List of message dictionaries containing conversation history
    """
    history: List[Dict[str, str]]


class ChatResponse(BaseModel):
    """
    Response model for chat API endpoint.
    
    Attributes:
        reply: The AI assistant's response message
    """
    reply: str
