"""
Error handling utilities for the AI Chat Assistant.

This module provides centralized error handling and logging functionality.
"""

import logging
from typing import Optional

import traceback

def handle_api_error(error: Exception, user_message: Optional[str] = None) -> str:
    """
    Handle API errors with logging and user-friendly messages.

    Args:
        error: The exception that occurred
        user_message: Optional user-friendly error message

    Returns:
        str: User-friendly error message to display
    """
    # Basic error handling logic
    logging.error("API Error: %s", str(error))
    logging.error(traceback.format_exc())
    if user_message:
        return user_message
    return "An error occurred. Please try again."


def handle_api_error(error: Exception, user_message: str = None) -> str:
    # Basic error handling logic
    logging.error(f"API Error: {error}")
    logging.error(traceback.format_exc())
    if user_message:
        return user_message
    return "An error occurred while processing your request. Please try again."
