"""
Learning Service for AI Chat Assistant

This service provides intelligent model selection based on user feedback
and performance data for continuous improvement.
"""

import time
from typing import Optional, Dict, Any, List

from database.feedback_manager import FeedbackManager
from utils.logger import get_logger, log_performance

logger = get_logger('learning_service')

class LearningService:
    """Service for intelligent model selection based on user feedback and performance data."""

    def __init__(self, feedback_manager: FeedbackManager):
        self.feedback_manager = feedback_manager
        self.model_cache = {}
        self.cache_timestamp = 0
        self.cache_ttl = 300  # 5 minutes cache

        logger.info("LearningService initialized")

    def get_optimal_model(self, conversation_style: str = 'helpful',
                         available_models: List[str] = None) -> str:
        """Get the optimal AI model based on learning data and feedback."""
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f"{conversation_style}_{hash(tuple(sorted(available_models or [])))}"
            current_time = time.time()

            if (cache_key in self.model_cache and
                current_time - self.cache_timestamp < self.cache_ttl):
                cached_model = self.model_cache[cache_key]
                logger.debug("Using cached optimal model: {cached_model}")
                return cached_model

            # Get best performing model from feedback data
            learned_model = self.feedback_manager.get_best_model_for_style(conversation_style)

            if learned_model and (not available_models or learned_model in available_models):
                # Use learned model if it's available
                selected_model = learned_model
                selection_reason = "feedback_based"
            else:
                # Fallback to available models with smart defaults
                if available_models:
                    selected_model = self._get_fallback_model(conversation_style, available_models)
                    selection_reason = "fallback_smart"
                else:
                    selected_model = "Gemini Pro"  # Default fallback
                    selection_reason = "default"

            # Update cache
            self.model_cache[cache_key] = selected_model
            self.cache_timestamp = current_time

            duration = time.time() - start_time
            log_performance("model_selection", duration,
                          selected_model=selected_model,
                          conversation_style=conversation_style,
                          selection_reason=selection_reason)

            logger.info("Selected optimal model: {selected_model} for style: {conversation_style} ({selection_reason})")

            return selected_model

        except Exception as error:
            logger.error("Failed to get optimal model: {e}")
            return available_models[0] if available_models else "Gemini Pro"

    def _get_fallback_model(self, conversation_style: str, available_models: List[str]) -> str:
        """Get smart fallback model based on conversation style."""

        # Style-based model preferences (when no feedback data available)
        style_preferences = {
            'professional': ['Gemini Pro', 'DialoGPT Large', 'DialoGPT Medium'],
            'creative': ['Gemini Pro', 'BlenderBot 400M', 'DialoGPT Large'],
            'analytical': ['Gemini Pro', 'DialoGPT Large', 'DialoGPT Medium'],
            'friendly': ['BlenderBot 400M', 'Gemini Pro', 'DialoGPT Medium'],
            'casual': ['BlenderBot 400M', 'DialoGPT Medium', 'Gemini Pro'],
            'helpful': ['Gemini Pro', 'DialoGPT Large', 'BlenderBot 400M']
        }

        preferred_models = style_preferences.get(conversation_style, ['Gemini Pro'])

        # Return first available preferred model
        for model in preferred_models:
            if model in available_models:
                return model

        # If no preferred model available, return first available
        return available_models[0]

    def record_model_performance(self, model_name: str, conversation_style: str,
                               response_time: float, success: bool) -> None:
        """Record model performance data for learning purposes."""
        try:
            performance_data = {
                'model': model_name,
                'style': conversation_style,
                'response_time': response_time,
                'success': success,
                'timestamp': time.time()
            }

            # Clear cache when new performance data is recorded
            self.model_cache.clear()

            logger.debug("Recorded performance data for {model_name}: {performance_data}")

        except Exception as error:
            logger.error("Failed to record model performance: {e}")

    def get_learning_recommendations(self) -> List[Dict[str, Any]]:
        """Get actionable recommendations based on learning data."""
        try:
            insights = self.feedback_manager.generate_learning_insights()

            recommendations = []
            for insight in insights:
                if insight['severity'] == 'high':
                    recommendations.append({
                        'priority': 'high',
                        'category': 'performance_issue',
                        'title': 'Model Performance Issue',
                        'description': insight['message'],
                        'action': insight['recommendation'],
                        'data': insight['data']
                    })
                elif insight['type'] == 'high_performer':
                    recommendations.append({
                        'priority': 'medium',
                        'category': 'optimization',
                        'title': 'Optimization Opportunity',
                        'description': insight['message'],
                        'action': insight['recommendation'],
                        'data': insight['data']
                    })

            return recommendations

        except Exception as error:
            logger.error("Failed to get learning recommendations: {e}")
            return []
