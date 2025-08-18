"""
Chat controller for handling LLM communication.

This module provides the business logic layer for chat operations,
coordinating between API endpoints and LLM services.
"""

from typing import List, Dict, Any

from services.llm_proxy import LLMProxy
from config.config import Config

llm_proxy = LLMProxy(Config.GEMINI_API_KEY)


def get_llm_reply(history: List[Dict[str, Any]]) -> str:
    """
    Get AI response for the given conversation history.

    Args:
        history: List of message dictionaries containing the conversation

    Returns:
        str: The AI assistant's response
    """
    return llm_proxy.send_message(history)
