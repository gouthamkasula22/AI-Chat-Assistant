"""
AI Models Package

This package contains all AI model implementations and strategies for the chat assistant.

Modules:
- ai_strategy: Abstract base classes and model management
- gemini_strategy: Google Gemini AI implementation
- huggingface_strategy: Hugging Face models implementation
- chat_models: API models for request/response structures

Classes:
- AIModelStrategy: Abstract base class for all AI models
- ModelManager: Manager for multiple AI models
- GeminiStrategy: Google Gemini implementation
- HuggingFaceStrategy: Hugging Face models implementation
"""

from .ai_strategy import AIModelStrategy, ModelManager, ModelConfig, ModelResponse, ModelProvider
from .gemini_strategy import GeminiStrategy, create_gemini_model
from .huggingface_strategy import (

    HuggingFaceStrategy,
    create_dialogpt_model,
    create_blenderbot_model,
    create_dialogpt_medium_model
)

__all__ = [
    'AIModelStrategy',
    'ModelManager',
    'ModelConfig',
    'ModelResponse',
    'ModelProvider',
    'GeminiStrategy',
    'create_gemini_model',
    'HuggingFaceStrategy',
    'create_dialogpt_model',
    'create_blenderbot_model',
    'create_dialogpt_medium_model'
]
