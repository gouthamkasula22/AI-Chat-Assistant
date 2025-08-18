"""
Hugging Face AI Model Implementation

This module implements AI model strategies using Hugging Face's free Inference API.
Hugging Face provides access to numerous open-source models at no cost.

Features:
- Multiple model options (Microsoft DialoGPT, Facebook BlenderBot, etc.)
- Completely free to use (rate limited)
- Support for conversational models
- Automatic model fallback
- No API key required for many models
"""

import requests
import time
import os
from typing import Dict, Any, List, Optional, Tuple
import logging
import json

from .ai_strategy import AIModelStrategy, ModelConfig, ModelResponse, ModelProvider

logger = logging.getLogger(__name__)


class HuggingFaceStrategy(AIModelStrategy):
    """
    Hugging Face model implementation.

    This strategy uses Hugging Face's free Inference API to access
    various open-source conversational AI models.
    """

    def __init__(self, model_name: str = "microsoft/DialoGPT-large",
                 api_token: Optional[str] = None):
        """
        Initialize Hugging Face strategy.

        Args:
            model_name (str): HuggingFace model identifier
            api_token (Optional[str]): HF API token for higher rate limits
        """
        # Model configurations for different HF models
        model_configs = {
            "microsoft/DialoGPT-large": ModelConfig(
                name="DialoGPT Large",
                provider=ModelProvider.HUGGINGFACE,
                model_id="microsoft/DialoGPT-large",
                description="Microsoft's conversational AI - Good for dialogue",
                max_tokens=1024,
                temperature=0.7,
                free_tier_limit=1000,
                requires_api_key=False
            ),
            "facebook/blenderbot-400M-distill": ModelConfig(
                name="BlenderBot 400M",
                provider=ModelProvider.HUGGINGFACE,
                model_id="facebook/blenderbot-400M-distill",
                description="Facebook's BlenderBot - Engaging conversations",
                max_tokens=512,
                temperature=0.8,
                free_tier_limit=1000,
                requires_api_key=False
            ),
            "microsoft/DialoGPT-medium": ModelConfig(
                name="DialoGPT Medium",
                provider=ModelProvider.HUGGINGFACE,
                model_id="microsoft/DialoGPT-medium",
                description="Microsoft's medium-size conversational model",
                max_tokens=1024,
                temperature=0.7,
                free_tier_limit=1000,
                requires_api_key=False
            )
        }

        config = model_configs.get(model_name, model_configs["microsoft/DialoGPT-large"])
        super().__init__(config)

        # API configuration
        self.api_token = api_token or os.getenv('HUGGINGFACE_API_TOKEN')
        self.base_url = "https://api-inference.huggingface.co/models"
        self.model_endpoint = f"{self.base_url}/{self.config.model_id}"

        # Rate limiting for free tier
        self.requests_per_hour = 1000 if self.api_token else 100
        self.request_timestamps = []

    def validate_configuration(self) -> Tuple[bool, str]:
        """
        Validate Hugging Face model configuration.

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Test model availability
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"

            # Test with a simple input
            test_payload = {
                "inputs": "Hello",
                "parameters": {
                    "max_length": 50,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }

            response = requests.post(
                self.model_endpoint,
                headers=headers,
                json=test_payload,
                timeout=30
            )

            if response.status_code == 200:
                return True, "Hugging Face model available"
            elif response.status_code == 503:
                return False, "Model is loading, please try again in a few minutes"
            elif response.status_code == 429:
                return False, "Rate limit exceeded"
            elif response.status_code == 401:
                return False, "Invalid Hugging Face API token"
            else:
                return False, f"Model unavailable: HTTP {response.status_code}"

        except requests.RequestException as error:
            return False, f"Connection failed: {str(error)}"

    def check_rate_limit(self) -> bool:
        """
        Check Hugging Face rate limits.

        Returns:
            bool: True if we can make a request
        """
        if not super().check_rate_limit():
            return False

        current_time = time.time()

        # Remove timestamps older than 1 hour
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if current_time - ts < 3600
        ]

        return len(self.request_timestamps) < self.requests_per_hour

    def generate_response(self, messages: List[Dict[str, str]],
                         session_id: str, **kwargs) -> ModelResponse:
        """
        Generate response using Hugging Face API.

        Args:
            messages (List[Dict[str, str]]): Conversation history
            session_id (str): Session identifier
            **kwargs: Additional parameters

        Returns:
            ModelResponse: Generated response
        """
        start_time = time.time()

        try:
            # Check rate limits
            if not self.check_rate_limit():
                return ModelResponse(
                    success=False,
                    content="",
                    response_time=time.time() - start_time,
                    model_used=self.config.name,
                    error_message="Rate limit exceeded for Hugging Face API",
                    provider=self.config.provider.value
                )

            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"

            # Format input for the model
            input_text = self._format_conversation_for_hf(messages)

            # Get parameters
            temperature = kwargs.get('temperature', self.config.temperature)
            max_tokens = kwargs.get('max_tokens', self.config.max_tokens)

            # Prepare payload based on model type
            if "DialoGPT" in self.config.model_id:
                payload = {
                    "inputs": input_text,
                    "parameters": {
                        "max_length": len(input_text.split()) + max_tokens,
                        "temperature": temperature,
                        "do_sample": True,
                        "top_p": self.config.top_p,
                        "return_full_text": False,
                        "pad_token_id": 50256
                    }
                }
            elif "blenderbot" in self.config.model_id:
                payload = {
                    "inputs": input_text,
                    "parameters": {
                        "max_length": max_tokens,
                        "temperature": temperature,
                        "do_sample": True
                    }
                }
            else:
                # Generic text generation
                payload = {
                    "inputs": input_text,
                    "parameters": {
                        "max_new_tokens": max_tokens,
                        "temperature": temperature,
                        "do_sample": True,
                        "return_full_text": False
                    }
                }

            # Make API request
            response = requests.post(
                self.model_endpoint,
                headers=headers,
                json=payload,
                timeout=60  # HF models can be slow
            )

            response_time = time.time() - start_time

            # Update usage tracking
            self.request_timestamps.append(time.time())
            self.update_usage()

            # Handle response
            if response.status_code == 200:
                result = response.json()

                # Extract generated text
                if isinstance(result, list) and len(result) > 0:
                    if "generated_text" in result[0]:
                        generated_text = result[0]["generated_text"]
                    elif "translation_text" in result[0]:
                        generated_text = result[0]["translation_text"]
                    else:
                        generated_text = str(result[0])

                    # Clean up the response
                    cleaned_response = self._clean_hf_response(generated_text, input_text)

                    return ModelResponse(
                        success=True,
                        content=cleaned_response,
                        response_time=response_time,
                        model_used=self.config.name,
                        tokens_used=self.calculate_token_estimate(cleaned_response),
                        provider=self.config.provider.value
                    )

                return ModelResponse(
                    success=False,
                    content="",
                    response_time=response_time,
                    model_used=self.config.name,
                    error_message="Unexpected response format from Hugging Face",
                    provider=self.config.provider.value
                )

            elif response.status_code == 503:
                error_msg = "Model is loading, please try again later"
            elif response.status_code == 429:
                error_msg = "Rate limit exceeded"
            else:
                try:
                    error_detail = response.json().get("error", "Unknown error")
                    error_msg = f"API error: {error_detail}"
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"

            return ModelResponse(
                success=False,
                content="",
                response_time=response_time,
                model_used=self.config.name,
                error_message=error_msg,
                provider=self.config.provider.value
            )

        except requests.Timeout:
            return self.handle_error(
                Exception("Request timeout"),
                "Hugging Face API request timed out"
            )
        except requests.RequestException as error:
            return self.handle_error(error, "Hugging Face API request failed")
        except Exception as error:
            return self.handle_error(error, "Unexpected error in Hugging Face strategy")

    def _format_conversation_for_hf(self, messages: List[Dict[str, str]]) -> str:
        """
        Format conversation for Hugging Face models.

        Args:
            messages (List[Dict[str, str]]): Message history

        Returns:
            str: Formatted input text
        """
        if not messages:
            return "Hello"

        # For DialoGPT, we want the conversation context
        if "DialoGPT" in self.config.model_id:
            # Take last few exchanges to stay within token limits
            recent_messages = messages[-6:] if len(messages) > 6 else messages

            conversation_parts = []
            for message in recent_messages:
                if message["role"] == "user":
                    conversation_parts.append(message["content"])
                else:
                    conversation_parts.append(message["content"])

            return " ".join(conversation_parts[-1:])  # Just the last user message

        # For BlenderBot and others, use the last user message
        last_user_message = None
        for message in reversed(messages):
            if message["role"] == "user":
                last_user_message = message["content"]
                break

        return last_user_message or "Hello"

    def _clean_hf_response(self, generated_text: str, input_text: str) -> str:
        """
        Clean up the response from Hugging Face models.

        Args:
            generated_text (str): Raw generated text
            input_text (str): Original input text

        Returns:
            str: Cleaned response
        """
        # Remove input text if it's included in the response
        if generated_text.startswith(input_text):
            generated_text = generated_text[len(input_text):].strip()

        # Clean up common artifacts
        generated_text = generated_text.strip()

        # Remove repetitive patterns
        sentences = generated_text.split('.')
        unique_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence not in unique_sentences:
                unique_sentences.append(sentence)

        cleaned = '. '.join(unique_sentences)
        if cleaned and not cleaned.endswith('.'):
            cleaned += '.'

        return cleaned if cleaned else "I understand. How can I help you further?"

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get Hugging Face specific model information.

        Returns:
            Dict[str, Any]: Extended model information
        """
        info = super().get_model_info()
        info.update({
            'api_token_configured': bool(self.api_token),
            'requests_per_hour': self.requests_per_hour,
            'current_hour_usage': len(self.request_timestamps),
            'model_endpoint': self.model_endpoint,
            'model_features': [
                'open_source',
                'free_tier',
                'conversational',
                'multilingual'
            ]
        })
        return info


# Factory functions for different HuggingFace models
def create_dialogpt_model(api_token: Optional[str] = None) -> HuggingFaceStrategy:
    """Create DialoGPT model instance."""
    return HuggingFaceStrategy("microsoft/DialoGPT-large", api_token)

def create_blenderbot_model(api_token: Optional[str] = None) -> HuggingFaceStrategy:
    """Create BlenderBot model instance."""
    return HuggingFaceStrategy("facebook/blenderbot-400M-distill", api_token)

def create_dialogpt_medium_model(api_token: Optional[str] = None) -> HuggingFaceStrategy:
    """Create DialoGPT Medium model instance."""
    return HuggingFaceStrategy("microsoft/DialoGPT-medium", api_token)
