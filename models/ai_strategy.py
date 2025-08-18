"""
AI Model Strategy Pattern Implementation

This module defines the abstract base class and concrete implementations for different AI models.
It follows the Strategy pattern to allow easy switching between AI providers while maintaining
a consistent interface.

Key Features:
- Abstract base class for all AI models
- Consistent API across different providers
- Configuration management for each model
- Error handling and fallback strategies
- Free tier usage tracking
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
import time

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Enumeration of supported AI model providers."""
    GEMINI = "gemini"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    TOGETHER = "together"


@dataclass
class ModelConfig:
    """Configuration class for AI models."""
    name: str
    provider: ModelProvider
    model_id: str
    description: str
    max_tokens: int = 2048
    temperature: float = 0.7
    free_tier_limit: int = 1000  # requests per day
    supports_streaming: bool = False
    requires_api_key: bool = True

    # Model-specific parameters
    top_p: float = 0.9
    top_k: int = 40
    repetition_penalty: float = 1.1


@dataclass
@dataclass
class ModelResponse:
    """Standardized response format for all AI models."""
    success: bool
    content: str
    response_time: float
    model_used: str
    tokens_used: int = 0
    error_message: Optional[str] = None

    # Additional metadata
    finish_reason: Optional[str] = None
    provider: Optional[str] = None


class AIModelStrategy(ABC):
    """
    Abstract base class for AI model strategies.

    This class defines the interface that all AI model implementations must follow.
    It ensures consistency across different providers and makes it easy to add new models.
    """

    def __init__(self, config: ModelConfig):
        """
        Initialize the AI model strategy.

        Args:
            config (ModelConfig): Configuration for this model
        """
        self.config = config
        self.usage_count = 0
        self.last_request_time = 0
        self.rate_limit_remaining = config.free_tier_limit

    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]],
                         session_id: str, **kwargs) -> ModelResponse:
        """
        Generate a response from the AI model.

        Args:
            messages (List[Dict[str, str]]): Conversation history
            session_id (str): Unique session identifier
            **kwargs: Additional model-specific parameters

        Returns:
            ModelResponse: Standardized response object
        """
        pass

    @abstractmethod
    def validate_configuration(self) -> Tuple[bool, str]:
        """
        Validate that the model is properly configured and available.

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        pass

    def check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits for this model.

        Returns:
            bool: True if we can make a request, False otherwise
        """
        current_time = time.time()

        # Reset daily limit if needed
        if current_time - self.last_request_time > 86400:  # 24 hours
            self.rate_limit_remaining = self.config.free_tier_limit
            self.usage_count = 0

        return self.rate_limit_remaining > 0

    def update_usage(self, tokens_used: int = 1):
        """
        Update usage statistics for rate limiting.

        Args:
            tokens_used (int): Number of tokens consumed in the request
        """
        self.usage_count += 1
        self.rate_limit_remaining -= 1
        self.last_request_time = time.time()

        logger.info(f"Model {self.config.name} usage: {self.usage_count} requests, "
                   f"{self.rate_limit_remaining} remaining")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about this model.

        Returns:
            Dict[str, Any]: Model information and statistics
        """
        return {
            'name': self.config.name,
            'provider': self.config.provider.value,
            'description': self.config.description,
            'usage_count': self.usage_count,
            'rate_limit_remaining': self.rate_limit_remaining,
            'supports_streaming': self.config.supports_streaming,
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature
        }

    def format_messages_for_model(self, messages: List[Dict[str, str]]) -> Any:
        """
        Format messages in the format expected by this specific model.

        Args:
            messages (List[Dict[str, str]]): Standard message format

        Returns:
            Any: Model-specific message format
        """
        # Default implementation - can be overridden by specific models
        return messages

    def calculate_token_estimate(self, text: str) -> int:
        """
        Estimate token count for rate limiting purposes.

        Args:
            text (str): Input text

        Returns:
            int: Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4

    def handle_error(self, error: Exception, context: str) -> ModelResponse:
        """
        Handle errors in a consistent way across all models.

        Args:
            error (Exception): The error that occurred
            context (str): Context description

        Returns:
            ModelResponse: Error response object
        """
        error_msg = f"{context}: {str(error)}"
        logger.error("Model {self.config.name} error: {error_msg}")

        return ModelResponse(
            success=False,
            content="",
            response_time=0.0,
            model_used=self.config.name,
            error_message=error_msg,
            provider=self.config.provider.value
        )


class ModelManager:
    """
    Manager class for handling multiple AI models.

    This class provides:
    - Model registration and discovery
    - Automatic fallback between models
    - Load balancing across available models
    - Health monitoring and model selection
    """

    def __init__(self):
        """Initialize the model manager."""
        self.models: Dict[str, AIModelStrategy] = {}
        self.default_model = None
        self.fallback_order = []

    def register_model(self, model: AIModelStrategy, is_default: bool = False):
        """
        Register a new AI model.

        Args:
            model (AIModelStrategy): The model strategy to register
            is_default (bool): Whether this should be the default model
        """
        self.models[model.config.name] = model

        if is_default or self.default_model is None:
            self.default_model = model.config.name

        logger.info(f"Registered AI model: {model.config.name} "
                   f"(provider: {model.config.provider.value})")

    def get_model(self, model_name: Optional[str] = None) -> Optional[AIModelStrategy]:
        """
        Get a specific model or the default model.

        Args:
            model_name (Optional[str]): Name of the model to get

        Returns:
            Optional[AIModelStrategy]: The requested model or None
        """
        if model_name is None:
            model_name = self.default_model

        return self.models.get(model_name)

    def get_available_models(self) -> List[str]:
        """
        Get list of all available model names.

        Returns:
            List[str]: List of available model names
        """
        available = []
        for name, model in self.models.items():
            is_valid, _ = model.validate_configuration()
            if is_valid and model.check_rate_limit():
                available.append(name)
        return available

    def generate_with_fallback(self, messages: List[Dict[str, str]],
                             session_id: str, preferred_model: Optional[str] = None,
                             **kwargs) -> ModelResponse:
        """
        Generate response with automatic fallback to other models if needed.

        Args:
            messages (List[Dict[str, str]]): Conversation history
            session_id (str): Session identifier
            preferred_model (Optional[str]): Preferred model name
            **kwargs: Additional parameters

        Returns:
            ModelResponse: Response from available model
        """
        # Determine model order to try
        models_to_try = []

        if preferred_model and preferred_model in self.models:
            models_to_try.append(preferred_model)

        if self.default_model and self.default_model not in models_to_try:
            models_to_try.append(self.default_model)

        # Add other available models
        for model_name in self.get_available_models():
            if model_name not in models_to_try:
                models_to_try.append(model_name)

        # Try each model in order
        for model_name in models_to_try:
            model = self.models.get(model_name)
            if not model:
                continue

            # Check if model is available
            is_valid, error_msg = model.validate_configuration()
            if not is_valid:
                logger.warning("Model {model_name} not available: {error_msg}")
                continue

            if not model.check_rate_limit():
                logger.warning("Model {model_name} rate limit exceeded")
                continue

            # Try to generate response
            try:
                response = model.generate_response(messages, session_id, **kwargs)
                if response.success:
                    logger.info("Successfully generated response using {model_name}")
                    return response
                else:
                    logger.warning("Model {model_name} failed: {response.error_message}")

            except Exception as error:
                logger.error("Unexpected error with model {model_name}: {error}")
                continue

        # If all models failed
        return ModelResponse(
            success=False,
            content="",
            response_time=0.0,
            model_used="none",
            error_message="All available AI models failed or are rate limited"
        )

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all models.

        Returns:
            Dict[str, Any]: System status information
        """
        status = {
            'total_models': len(self.models),
            'default_model': self.default_model,
            'models': {}
        }

        for name, model in self.models.items():
            is_valid, error_msg = model.validate_configuration()
            model_info = model.get_model_info()
            model_info.update({
                'is_available': is_valid,
                'error_message': error_msg if not is_valid else None,
                'within_rate_limit': model.check_rate_limit()
            })
            status['models'][name] = model_info

        return status
