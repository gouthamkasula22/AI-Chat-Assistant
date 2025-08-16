import unittest
from unittest.mock import Mock, patch, MagicMock
from models.ai_strategy import AIModelStrategy, ModelManager, ModelConfig, ModelProvider, ModelResponse


class MockAIStrategy(AIModelStrategy):
    """Mock AI strategy for testing"""
    
    def __init__(self, name="MockModel", provider=ModelProvider.HUGGINGFACE, available=True, rate_limited=False):
        config = ModelConfig(
            name=name,
            provider=provider,
            model_id="mock/model",
            description="Mock model for testing"
        )
        super().__init__(config)
        self._available = available
        self._rate_limited = rate_limited
        
    def generate_response(self, messages, session_id, **kwargs):
        if not self._available:
            raise Exception("Model not available")
        if self._rate_limited:
            raise Exception("Rate limit exceeded")
        
        return ModelResponse(
            success=True,
            content=f"Mock response from {self.config.name}",
            response_time=0.1,
            model_used=self.config.name,
            tokens_used=10,
            provider=self.config.provider.value
        )
    
    def validate_configuration(self):
        if self._available:
            return True, "Configuration valid"
        else:
            return False, "Mock model not available"


class TestAIStrategy(unittest.TestCase):
    def test_mock_strategy_basic_functionality(self):
        """Test basic functionality of mock strategy"""
        strategy = MockAIStrategy("TestModel", ModelProvider.HUGGINGFACE)
        
        self.assertEqual(strategy.config.name, "TestModel")
        self.assertEqual(strategy.config.provider, ModelProvider.HUGGINGFACE)

    def test_mock_strategy_response_generation(self):
        """Test response generation"""
        strategy = MockAIStrategy("TestModel", ModelProvider.HUGGINGFACE)
        
        response = strategy.generate_response([], "test_session")
        self.assertIsInstance(response, ModelResponse)
        self.assertTrue(response.success)
        self.assertIn("Mock response from TestModel", response.content)

    def test_strategy_unavailable(self):
        """Test behavior when strategy is unavailable"""
        strategy = MockAIStrategy("TestModel", ModelProvider.HUGGINGFACE, available=False)
        
        is_valid, _ = strategy.validate_configuration()
        self.assertFalse(is_valid)
        
        with self.assertRaises(Exception):
            strategy.generate_response([], "test_session")

    def test_strategy_rate_limited(self):
        """Test behavior when strategy is rate limited"""
        strategy = MockAIStrategy("TestModel", ModelProvider.HUGGINGFACE, rate_limited=True)
        
        with self.assertRaises(Exception):
            strategy.generate_response([], "test_session")


class TestModelManager(unittest.TestCase):
    def setUp(self):
        """Set up test model manager"""
        self.model_manager = ModelManager()

    def test_register_model(self):
        """Test registering AI models"""
        strategy = MockAIStrategy("TestModel", ModelProvider.HUGGINGFACE)
        self.model_manager.register_model(strategy)
        
        models = self.model_manager.get_available_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0], "TestModel")

    def test_register_multiple_models(self):
        """Test registering multiple AI models"""
        strategy1 = MockAIStrategy("Model1", ModelProvider.GEMINI)
        strategy2 = MockAIStrategy("Model2", ModelProvider.HUGGINGFACE)
        
        self.model_manager.register_model(strategy1)
        self.model_manager.register_model(strategy2)
        
        models = self.model_manager.get_available_models()
        self.assertEqual(len(models), 2)

    def test_get_model_by_name(self):
        """Test retrieving specific model by name"""
        strategy = MockAIStrategy("SpecificModel", ModelProvider.HUGGINGFACE)
        self.model_manager.register_model(strategy)
        
        retrieved = self.model_manager.get_model("SpecificModel")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.config.name, "SpecificModel")

    def test_get_nonexistent_model(self):
        """Test retrieving non-existent model"""
        retrieved = self.model_manager.get_model("NonExistent")
        self.assertIsNone(retrieved)

    def test_generate_with_fallback(self):
        """Test generating response with fallback logic"""
        # Create models with different availability
        available_model = MockAIStrategy("Available", ModelProvider.HUGGINGFACE, available=True)
        unavailable_model = MockAIStrategy("Unavailable", ModelProvider.GEMINI, available=False)
        
        self.model_manager.register_model(unavailable_model)
        self.model_manager.register_model(available_model)
        
        # Should fall back to available model
        response = self.model_manager.generate_with_fallback(
            messages=[], session_id="test", preferred_model="Unavailable"
        )
        
        self.assertTrue(response.success)
        self.assertIn("Available", response.content)

    def test_preferred_model_rate_limited(self):
        """Test fallback when preferred model is rate limited"""
        rate_limited = MockAIStrategy("RateLimited", ModelProvider.GEMINI, rate_limited=True)
        available = MockAIStrategy("Available", ModelProvider.HUGGINGFACE)
        
        self.model_manager.register_model(rate_limited)
        self.model_manager.register_model(available)
        
        response = self.model_manager.generate_with_fallback(
            messages=[], session_id="test", preferred_model="RateLimited"
        )
        
        self.assertTrue(response.success)
        self.assertIn("Available", response.content)


if __name__ == '__main__':
    unittest.main()
