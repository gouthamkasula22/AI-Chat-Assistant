"""
Google Gemini AI Model Implementation

This module implements the Gemini AI model strategy using Google's Gemini API.
Gemini offers a generous free tier with good performance for conversational AI.

Features:
- Gemini Pro model integration
- Free tier: 15 requests per minute, 1500 requests per day
- Support for conversation context
- Configurable temperature and safety settings
- Proper error handling and rate limiting
"""

import requests
import time
import os
from typing import Dict, Any, List, Optional, Tuple
import logging

from .ai_strategy import AIModelStrategy, ModelConfig, ModelResponse, ModelProvider

logger = logging.getLogger(__name__)


class GeminiStrategy(AIModelStrategy):
    """
    Google Gemini AI model implementation.

    This strategy implements the Gemini Pro model with conversation awareness
    and proper rate limiting for the free tier.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini strategy.

        Args:
            api_key (Optional[str]): Gemini API key. If None, reads from environment.
        """
        config = ModelConfig(
            name="Gemini Pro",
            provider=ModelProvider.GEMINI,
            model_id="gemini-1.5-flash",
            description="Google's Gemini Flash - Fast and capable conversational AI",
            max_tokens=2048,
            temperature=0.7,
            free_tier_limit=1500,  # 1500 requests per day
            supports_streaming=False,
            requires_api_key=True
        )

        super().__init__(config)

        # Get API key
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')

        # API endpoints
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.generate_endpoint = f"{self.base_url}/models/{self.config.model_id}:generateContent"

        # Rate limiting for free tier (15 requests per minute)
        self.requests_per_minute = 15
        self.request_timestamps = []

    def validate_configuration(self) -> Tuple[bool, str]:
        """
        Validate Gemini configuration.

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not self.api_key:
            return False, "Gemini API key not found. Please set GEMINI_API_KEY environment variable."

        # Test API connection
        try:
            test_url = f"{self.base_url}/models/{self.config.model_id}"
            response = requests.get(
                test_url,
                params={"key": self.api_key},
                timeout=10
            )

            if response.status_code == 200:
                return True, "Gemini API connection successful"
            elif response.status_code == 401:
                return False, "Invalid Gemini API key"
            else:
                return False, f"Gemini API error: {response.status_code}"

        except requests.RequestException as error:
            return False, f"Gemini API connection failed: {str(error)}"

    def check_rate_limit(self) -> bool:
        """
        Check Gemini-specific rate limits.

        Returns:
            bool: True if we can make a request
        """
        # Check base rate limit first
        if not super().check_rate_limit():
            return False

        # Check per-minute rate limit
        current_time = time.time()

        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if current_time - ts < 60
        ]

        # Check if we can make another request
        return len(self.request_timestamps) < self.requests_per_minute

    def generate_response(self, messages: List[Dict[str, str]],
                         session_id: str, **kwargs) -> ModelResponse:
        """
        Generate response using Gemini API.

        Args:
            messages (List[Dict[str, str]]): Conversation history
            session_id (str): Session identifier
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

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
                    error_message="Rate limit exceeded for Gemini API",
                    provider=self.config.provider.value
                )

            # Prepare the request
            prompt = self._format_conversation_for_gemini(messages)

            # Get parameters
            temperature = kwargs.get('temperature', self.config.temperature)
            max_tokens = kwargs.get('max_tokens', self.config.max_tokens)

            # Prepare request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "topK": self.config.top_k,
                    "topP": self.config.top_p,
                    "maxOutputTokens": max_tokens,
                    "stopSequences": []
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }

            # Make API request
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            response_time = time.time() - start_time

            # Update rate limiting
            self.request_timestamps.append(time.time())
            self.update_usage()

            # Handle response
            if response.status_code == 200:
                result = response.json()

                # Extract content
                if 'candidates' in result and result['candidates']:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        content = candidate['content']['parts'][0].get('text', '')

                        # Get finish reason
                        finish_reason = candidate.get('finishReason', 'STOP')

                        return ModelResponse(
                            success=True,
                            content=content.strip(),
                            response_time=response_time,
                            model_used=self.config.name,
                            tokens_used=self.calculate_token_estimate(content),
                            finish_reason=finish_reason,
                            provider=self.config.provider.value
                        )

                # If we get here, the response format was unexpected
                return ModelResponse(
                    success=False,
                    content="",
                    response_time=response_time,
                    model_used=self.config.name,
                    error_message="Unexpected response format from Gemini API",
                    provider=self.config.provider.value
                )

            else:
                # Handle API errors
                error_msg = f"Gemini API error {response.status_code}"
                try:
                    error_detail = response.json().get('error', {}).get('message', '')
                    if error_detail:
                        error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text[:200]}"

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
                "Gemini API request timed out"
            )
        except requests.RequestException as error:
            return self.handle_error(error, "Gemini API request failed")
        except Exception as error:
            return self.handle_error(error, "Unexpected error in Gemini strategy")

    def _format_conversation_for_gemini(self, messages: List[Dict[str, str]]) -> str:
        """
        Format conversation history for Gemini API.

        Args:
            messages (List[Dict[str, str]]): Message history

        Returns:
            str: Formatted prompt for Gemini
        """
        if not messages:
            return "Hello! How can I help you today?"

        # Build conversation context
        conversation_parts = []

        for message in messages[:-1]:  # All except the last message
            role = "Human" if message["role"] == "user" else "Assistant"
            conversation_parts.append(f"{role}: {message['content']}")

        # Add the current user message
        last_message = messages[-1]
        if last_message["role"] == "user":
            conversation_parts.append(f"Human: {last_message['content']}")

        # Add instruction for assistant response
        conversation_parts.append("Assistant:")

        return "\n\n".join(conversation_parts)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get Gemini-specific model information.

        Returns:
            Dict[str, Any]: Extended model information
        """
        info = super().get_model_info()
        info.update({
            'api_key_configured': bool(self.api_key),
            'requests_per_minute': self.requests_per_minute,
            'current_minute_usage': len(self.request_timestamps),
            'model_features': [
                'conversational_ai',
                'safety_filters',
                'multi_language',
                'context_aware'
            ]
        })
        return info


# Factory function for easy model creation
def create_gemini_model(api_key: Optional[str] = None) -> GeminiStrategy:
    """
    Factory function to create a Gemini model instance.

    Args:
        api_key (Optional[str]): API key for Gemini

    Returns:
        GeminiStrategy: Configured Gemini model
    """
    return GeminiStrategy(api_key)
