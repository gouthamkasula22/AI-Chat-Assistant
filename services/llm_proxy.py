"""
LLM Proxy service for Google Gemini API integration.

This module handles communication with the Google Gemini API and provides
error handling for various failure scenarios.
"""

from typing import List, Dict, Any
import requests
from utils.error_handler import handle_api_error


class LLMProxy:
    """Proxy class for communicating with Google Gemini LLM API."""

    def __init__(self, api_key: str) -> None:
        """
        Initialize the LLM proxy with API credentials.
        
        Args:
            api_key: Google AI API key for authentication
        """
        self.api_key = api_key

    def send_message(self, history: List[Dict[str, Any]]) -> str:
        """
        Send message history to Google Gemini API and get response.
        
        Args:
            history: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            str: The AI assistant's response text
        """
        # Filter out invalid messages
        filtered_history = [msg for msg in history if msg.get("role") and msg.get("content")]

        filtered_history = filtered_history[-10:]

        if not filtered_history or filtered_history[0]["role"] != "user":
            return "Conversation must start with a user message."

        # Build payload
        payload = {
            "contents": [
                {
                    "role": msg["role"] if msg["role"] == "user" else "model",
                    "parts": [{"text": msg["content"]}],
                }
                for msg in filtered_history
            ]
        }

        # API request
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        try:
            response = requests.post(
                url, headers=headers, params=params, json=payload, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

        except requests.exceptions.RequestException as exception:
            if isinstance(exception, requests.exceptions.Timeout):
                user_message = "Request timed out. Please try again later."
            elif isinstance(exception, requests.exceptions.HTTPError):
                user_message = (
                    f"HTTP error: {exception.response.status_code} - "
                    f"{exception.response.reason}"
                )
            else:
                user_message = "Network error occurred. Please check your connection."
            return handle_api_error(exception, user_message)

        except Exception as exception:
            return handle_api_error(exception, "An unexpected error occurred.")
