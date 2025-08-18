"""
Configuration management for the AI Chat Assistant.

This module handles environment variables and application configuration.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Application configuration class.

    Attributes:
        GEMINI_API_KEY: Google AI API key from environment variables
    """
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
