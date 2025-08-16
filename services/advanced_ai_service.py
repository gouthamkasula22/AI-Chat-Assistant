"""
Advanced AI Service

This service provides advanced AI features including:
- Multiple AI model support with automatic fallback
- Personality modes and conversation styles
- Dynamic model selection based on context
- Response quality optimization
- Usage analytics and monitoring

Features:
- Model management and health monitoring
- Conversation style adaptation
- Automatic model fallback and load balancing
- Response post-processing and enhancement
- Usage tracking and analytics
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import time
import json

from models.ai_strategy import ModelManager, ModelResponse
from models.gemini_strategy import create_gemini_model
from models.huggingface_strategy import (
    create_dialogpt_model, 
    create_blenderbot_model,
    create_dialogpt_medium_model
)

logger = logging.getLogger(__name__)


class ConversationStyle(Enum):
    """Different conversation styles/personalities."""
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional" 
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    CASUAL = "casual"
    HELPFUL = "helpful"


class AdvancedAIService:
    """
    Advanced AI service that manages multiple models and provides enhanced features.
    
    This service acts as the main interface for all AI operations, providing:
    - Multiple model support with automatic fallback
    - Conversation style management
    - Response optimization and post-processing
    - Usage analytics and health monitoring
    """
    
    def __init__(self):
        """Initialize the advanced AI service."""
        self.model_manager = ModelManager()
        self.conversation_styles = {}
        self.usage_analytics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'model_usage': {},
            'average_response_time': 0,
            'style_usage': {}
        }
        
        # Initialize conversation style prompts
        self._initialize_conversation_styles()
        
        # Register available models
        self._register_models()
        
        logger.info("Advanced AI Service initialized")
    
    def _initialize_conversation_styles(self):
        """Initialize conversation style system prompts."""
        self.conversation_styles = {
            ConversationStyle.FRIENDLY: {
                "name": "Friendly Assistant",
                "description": "Warm, approachable, and encouraging",
                "prompt_prefix": "You are a friendly and warm AI assistant. Be encouraging, use a conversational tone, and show empathy. Use casual language while remaining helpful.",
                "temperature": 0.8,
                "personality_traits": ["warm", "encouraging", "empathetic", "conversational"]
            },
            ConversationStyle.PROFESSIONAL: {
                "name": "Professional Assistant", 
                "description": "Formal, precise, and business-oriented",
                "prompt_prefix": "You are a professional AI assistant. Provide clear, concise, and accurate responses. Use formal language and focus on efficiency and precision.",
                "temperature": 0.6,
                "personality_traits": ["formal", "precise", "efficient", "authoritative"]
            },
            ConversationStyle.CREATIVE: {
                "name": "Creative Assistant",
                "description": "Imaginative, innovative, and inspirational", 
                "prompt_prefix": "You are a creative AI assistant. Think outside the box, offer innovative ideas, and inspire creativity. Use vivid language and encourage exploration of new possibilities.",
                "temperature": 0.9,
                "personality_traits": ["imaginative", "innovative", "inspiring", "artistic"]
            },
            ConversationStyle.ANALYTICAL: {
                "name": "Analytical Assistant",
                "description": "Logical, data-driven, and systematic",
                "prompt_prefix": "You are an analytical AI assistant. Provide logical, well-reasoned responses. Break down complex problems, use data when possible, and explain your reasoning step by step.",
                "temperature": 0.5,
                "personality_traits": ["logical", "systematic", "data-driven", "methodical"]
            },
            ConversationStyle.CASUAL: {
                "name": "Casual Assistant",
                "description": "Relaxed, informal, and conversational",
                "prompt_prefix": "You are a casual AI assistant. Keep things relaxed and informal. Use everyday language, be conversational, and don't be afraid to use humor when appropriate.",
                "temperature": 0.7,
                "personality_traits": ["relaxed", "informal", "humorous", "conversational"]
            },
            ConversationStyle.HELPFUL: {
                "name": "Helpful Assistant",
                "description": "Solution-focused and resourceful",
                "prompt_prefix": "You are a helpful AI assistant focused on providing practical solutions. Always try to be as useful as possible, offer concrete suggestions, and go the extra mile to help.",
                "temperature": 0.7,
                "personality_traits": ["solution-focused", "resourceful", "practical", "supportive"]
            }
        }
    
    def _register_models(self):
        """Register all available AI models."""
        try:
            # Register Gemini (primary model)
            gemini_model = create_gemini_model()
            self.model_manager.register_model(gemini_model, is_default=True)
            
            # Register Hugging Face models as fallbacks
            dialogpt_model = create_dialogpt_model()
            self.model_manager.register_model(dialogpt_model)
            
            blenderbot_model = create_blenderbot_model()
            self.model_manager.register_model(blenderbot_model)
            
            dialogpt_medium_model = create_dialogpt_medium_model()
            self.model_manager.register_model(dialogpt_medium_model)
            
            logger.info("All AI models registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register AI models: {e}")
    
    def generate_response(self, messages: List[Dict[str, str]], session_id: str,
                         style: ConversationStyle = ConversationStyle.HELPFUL,
                         preferred_model: Optional[str] = None,
                         **kwargs) -> ModelResponse:
        """
        Generate an AI response with advanced features.
        
        Args:
            messages (List[Dict[str, str]]): Conversation history
            session_id (str): Session identifier
            style (ConversationStyle): Desired conversation style
            preferred_model (Optional[str]): Preferred AI model
            **kwargs: Additional parameters
            
        Returns:
            ModelResponse: Enhanced AI response
        """
        start_time = time.time()
        
        try:
            # Update analytics
            self.usage_analytics['total_requests'] += 1
            self.usage_analytics['style_usage'][style.value] = \
                self.usage_analytics['style_usage'].get(style.value, 0) + 1
            
            # Apply conversation style
            enhanced_messages = self._apply_conversation_style(messages, style)
            
            # Get style-specific parameters
            style_config = self.conversation_styles[style]
            temperature = kwargs.get('temperature', style_config['temperature'])
            
            # Generate response using model manager
            response = self.model_manager.generate_with_fallback(
                messages=enhanced_messages,
                session_id=session_id,
                preferred_model=preferred_model,
                temperature=temperature,
                **kwargs
            )
            
            # Post-process the response
            if response.success:
                response.content = self._post_process_response(
                    response.content, style, enhanced_messages
                )
                self.usage_analytics['successful_requests'] += 1
                
                # Update model usage analytics
                model_name = response.model_used
                self.usage_analytics['model_usage'][model_name] = \
                    self.usage_analytics['model_usage'].get(model_name, 0) + 1
            else:
                self.usage_analytics['failed_requests'] += 1
            
            # Update average response time
            total_time = time.time() - start_time
            current_avg = self.usage_analytics['average_response_time']
            total_requests = self.usage_analytics['total_requests']
            self.usage_analytics['average_response_time'] = \
                (current_avg * (total_requests - 1) + total_time) / total_requests
            
            return response
            
        except Exception as e:
            logger.error(f"Error in advanced AI service: {e}")
            self.usage_analytics['failed_requests'] += 1
            
            return ModelResponse(
                success=False,
                content="",
                response_time=time.time() - start_time,
                model_used="none",
                error_message=f"Advanced AI service error: {str(e)}"
            )
    
    def _apply_conversation_style(self, messages: List[Dict[str, str]], 
                                style: ConversationStyle) -> List[Dict[str, str]]:
        """
        Apply conversation style to the message history.
        
        Args:
            messages (List[Dict[str, str]]): Original messages
            style (ConversationStyle): Desired style
            
        Returns:
            List[Dict[str, str]]: Enhanced messages with style applied
        """
        if not messages:
            return messages
        
        style_config = self.conversation_styles[style]
        enhanced_messages = messages.copy()
        
        # Add system prompt if this is the first interaction
        if len(messages) <= 1:
            system_message = {
                "role": "system",
                "content": style_config["prompt_prefix"]
            }
            enhanced_messages = [system_message] + enhanced_messages
        
        return enhanced_messages
    
    def _post_process_response(self, content: str, style: ConversationStyle,
                             messages: List[Dict[str, str]]) -> str:
        """
        Post-process the AI response to enhance quality.
        
        Args:
            content (str): Original response content
            style (ConversationStyle): Conversation style used
            messages (List[Dict[str, str]]): Message context
            
        Returns:
            str: Enhanced response content
        """
        if not content:
            return content
        
        # Remove common artifacts
        content = content.strip()
        
        # Remove system prompts that might have leaked through
        if content.startswith("You are"):
            lines = content.split('\n')
            content = '\n'.join(lines[1:]).strip()
        
        # Style-specific post-processing
        style_config = self.conversation_styles[style]
        
        if style == ConversationStyle.PROFESSIONAL:
            # Ensure professional tone
            content = self._ensure_professional_tone(content)
        elif style == ConversationStyle.FRIENDLY:
            # Add friendly touches if missing
            content = self._add_friendly_touches(content)
        elif style == ConversationStyle.CREATIVE:
            # Enhance creative elements
            content = self._enhance_creativity(content)
        
        # General quality improvements
        content = self._improve_response_quality(content)
        
        return content
    
    def _ensure_professional_tone(self, content: str) -> str:
        """Ensure professional tone in responses."""
        # Replace casual phrases with professional ones
        replacements = {
            "yeah": "yes",
            "gonna": "going to", 
            "wanna": "want to",
            "kinda": "somewhat",
            "sorta": "somewhat"
        }
        
        for casual, formal in replacements.items():
            content = content.replace(casual, formal)
        
        return content
    
    def _add_friendly_touches(self, content: str) -> str:
        """Add friendly elements to responses."""
        if not content:
            return content
        
        # Add encouraging phrases occasionally
        friendly_additions = [
            "I hope this helps!",
            "Feel free to ask if you need more clarification!",
            "I'm here to help!",
            "Let me know if you have other questions!"
        ]
        
        # Add friendly touch if response seems too dry
        if len(content) > 50 and not any(phrase in content.lower() for phrase in 
                                       ["hope", "feel free", "let me know", "happy to"]):
            import random
            addition = random.choice(friendly_additions)
            content += f" {addition}"
        
        return content
    
    def _enhance_creativity(self, content: str) -> str:
        """Enhance creative elements in responses."""
        # This could include adding more vivid language, metaphors, etc.
        # For now, just ensure the response encourages creative thinking
        if "creative" not in content.lower() and "imagine" not in content.lower():
            if len(content) > 100:
                content += " Feel free to explore creative possibilities with this!"
        
        return content
    
    def _improve_response_quality(self, content: str) -> str:
        """General response quality improvements."""
        # Remove excessive repetition
        sentences = content.split('.')
        unique_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not any(sentence.lower() in existing.lower() 
                                  for existing in unique_sentences):
                unique_sentences.append(sentence)
        
        improved_content = '. '.join(unique_sentences)
        
        # Ensure proper ending
        if improved_content and not improved_content.endswith(('.', '!', '?')):
            improved_content += '.'
        
        return improved_content
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get information about all available models.
        
        Returns:
            List[Dict[str, Any]]: List of available models with their info
        """
        available_models = []
        
        for model_name in self.model_manager.models:
            model = self.model_manager.get_model(model_name)
            if model:
                model_info = model.get_model_info()
                is_valid, error_msg = model.validate_configuration()
                
                model_info.update({
                    'is_available': is_valid,
                    'error_message': error_msg if not is_valid else None,
                    'within_rate_limit': model.check_rate_limit()
                })
                
                available_models.append(model_info)
        
        return available_models
    
    def get_conversation_styles(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about available conversation styles.
        
        Returns:
            Dict[str, Dict[str, Any]]: Style information
        """
        return {
            style.value: {
                'name': config['name'],
                'description': config['description'],
                'personality_traits': config['personality_traits'],
                'temperature': config['temperature']
            }
            for style, config in self.conversation_styles.items()
        }
    
    def get_service_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics about the AI service.
        
        Returns:
            Dict[str, Any]: Service analytics and health metrics
        """
        # Get model system status
        model_status = self.model_manager.get_system_status()
        
        # Calculate success rate
        total_requests = self.usage_analytics['total_requests']
        success_rate = 0
        if total_requests > 0:
            success_rate = (self.usage_analytics['successful_requests'] / total_requests) * 100
        
        return {
            'usage_analytics': self.usage_analytics,
            'success_rate_percentage': round(success_rate, 2),
            'model_system_status': model_status,
            'available_styles': len(self.conversation_styles),
            'service_health': 'healthy' if success_rate > 80 else 'degraded',
            'features': [
                'multi_model_support',
                'conversation_styles',
                'automatic_fallback',
                'response_optimization',
                'usage_analytics'
            ]
        }
    
    def set_preferred_model(self, model_name: str) -> bool:
        """
        Set the preferred model for the service.
        
        Args:
            model_name (str): Name of the model to set as preferred
            
        Returns:
            bool: True if successful, False otherwise
        """
        if model_name in self.model_manager.models:
            self.model_manager.default_model = model_name
            logger.info(f"Set preferred model to: {model_name}")
            return True
        
        logger.warning(f"Model not found: {model_name}")
        return False
    
    def test_model_connectivity(self) -> Dict[str, Dict[str, Any]]:
        """
        Test connectivity and health of all registered models.
        
        Returns:
            Dict[str, Dict[str, Any]]: Test results for each model
        """
        test_results = {}
        
        for model_name, model in self.model_manager.models.items():
            start_time = time.time()
            is_valid, error_msg = model.validate_configuration()
            test_time = time.time() - start_time
            
            test_results[model_name] = {
                'is_available': is_valid,
                'response_time': test_time,
                'error_message': error_msg if not is_valid else None,
                'rate_limit_ok': model.check_rate_limit(),
                'model_info': model.get_model_info()
            }
        
        return test_results
