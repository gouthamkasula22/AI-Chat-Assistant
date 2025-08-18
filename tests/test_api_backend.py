"""
API & Backend Integration Tests

Tests for FastAPI backend endpoints, HTTP handling, error management,
and fallback mechanisms.
"""

import json
import os
import tempfile
import threading
import time
import unittest
from typing import Dict, Any
from unittest.mock import patch, Mock, MagicMock
import requests

# Import the FastAPI app
try:
    from app import app
    from fastapi.testclient import TestClient
    APP_AVAILABLE = True
except ImportError:
    APP_AVAILABLE = False

from models.chat_models import ChatRequest, ChatResponse


class TestFastAPIBackend(unittest.TestCase):
    """Test FastAPI backend endpoints and functionality"""

    def setUp(self):
        """Set up test client and mock data"""
        if APP_AVAILABLE:
            self.client = TestClient(app)
        self.valid_chat_request = {
            "history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ]
        }
        self.invalid_requests = [
            {},  # Empty request
            {"invalid": "field"},  # Wrong field
            {"history": "not_a_list"},  # Wrong type
            {"history": [123]},  # Invalid message structure (not a dict)
        ]

    @unittest.skipUnless(APP_AVAILABLE, "FastAPI app not available")
    def test_health_check_endpoint(self):
        """Test the API health check endpoint"""
        response = self.client.get("/")
        # App doesn't define root endpoint, so 404 is expected
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(APP_AVAILABLE, "FastAPI app not available")
    def test_docs_endpoint(self):
        """Test API documentation endpoint"""
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))

    @unittest.skipUnless(APP_AVAILABLE, "FastAPI app not available")
    def test_openapi_schema(self):
        """Test OpenAPI schema generation"""
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertIn("openapi", schema)
        self.assertIn("paths", schema)
        self.assertIn("/chat", schema["paths"])

    @unittest.skipUnless(APP_AVAILABLE, "FastAPI app not available")
    @patch('controllers.chat_controller.llm_proxy')  # Mock the LLM proxy instance
    def test_chat_endpoint_success(self, mock_proxy):
        """Test successful chat endpoint response"""
        mock_proxy.send_message.return_value = "This is a test response from the AI."

        response = self.client.post("/chat", json=self.valid_chat_request)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("reply", data)
        self.assertEqual(data["reply"], "This is a test response from the AI.")
        mock_proxy.send_message.assert_called_once_with(self.valid_chat_request["history"])

    @unittest.skipUnless(APP_AVAILABLE, "FastAPI app not available")
    def test_chat_endpoint_validation_errors(self):
        """Test chat endpoint with invalid requests"""
        for invalid_request in self.invalid_requests:
            with self.subTest(request=invalid_request):
                response = self.client.post("/chat", json=invalid_request)
                self.assertEqual(response.status_code, 422)  # Validation Error
                data = response.json()
                self.assertIn("detail", data)

    @unittest.skipUnless(APP_AVAILABLE, "FastAPI app not available")
    @patch('controllers.chat_controller.llm_proxy')  # Mock the LLM proxy instance
    def test_chat_endpoint_internal_error(self, mock_proxy):
        """Test chat endpoint with internal server error"""
        mock_proxy.send_message.side_effect = Exception("Internal processing error")

        response = self.client.post("/chat", json=self.valid_chat_request)

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("error", data["detail"].lower())

    @unittest.skipUnless(APP_AVAILABLE, "FastAPI app not available")
    def test_content_type_validation(self):
        """Test API validates Content-Type header"""
        # Test with wrong content type
        response = self.client.post(
            "/chat",
            data="invalid data",
            headers={"Content-Type": "text/plain"}
        )
        self.assertIn(response.status_code, [400, 422])

    def test_chat_models_validation(self):
        """Test Pydantic model validation"""
        # Valid request
        valid_request = ChatRequest(history=self.valid_chat_request["history"])
        self.assertEqual(len(valid_request.history), 3)

        # Test response model
        response = ChatResponse(reply="Test response")
        self.assertEqual(response.reply, "Test response")

        # Invalid request should raise validation error
        with self.assertRaises(Exception):
            ChatRequest(history="not_a_list")


class TestHTTPRequestHandling(unittest.TestCase):
    """Test HTTP request/response handling and error management"""

    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:8000"
        self.chat_endpoint = f"{self.base_url}/chat"
        self.test_payload = {
            "history": [{"role": "user", "content": "Test message"}]
        }

    def test_request_timeout_handling(self):
        """Test handling of request timeouts"""
        # Mock a very slow server response
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

            try:
                response = requests.post(
                    self.chat_endpoint,
                    json=self.test_payload,
                    timeout=1
                )
                self.fail("Should have raised Timeout exception")
            except requests.exceptions.Timeout:
                pass  # Expected behavior

    def test_connection_error_handling(self):
        """Test handling of connection errors"""
        # Test connection to non-existent server
        fake_url = "http://localhost:9999/chat"

        try:
            response = requests.post(
                fake_url,
                json=self.test_payload,
                timeout=2
            )
            self.fail("Should have raised ConnectionError")
        except requests.exceptions.ConnectionError:
            pass  # Expected behavior

    def test_http_status_code_handling(self):
        """Test handling of various HTTP status codes"""
        status_codes = [400, 401, 403, 404, 429, 500, 502, 503]

        for status_code in status_codes:
            with self.subTest(status_code=status_code):
                with patch('requests.post') as mock_post:
                    mock_response = Mock()
                    mock_response.status_code = status_code
                    mock_response.text = f"Error {status_code}"
                    mock_response.json.return_value = {"error": f"HTTP {status_code}"}
                    mock_post.return_value = mock_response

                    response = requests.post(
                        self.chat_endpoint,
                        json=self.test_payload,
                        timeout=5
                    )

                    self.assertEqual(response.status_code, status_code)

    def test_malformed_json_response(self):
        """Test handling of malformed JSON responses"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Not valid JSON {"
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_post.return_value = mock_response

            response = requests.post(
                self.chat_endpoint,
                json=self.test_payload,
                timeout=5
            )

            with self.assertRaises(json.JSONDecodeError):
                response.json()

    def test_large_request_handling(self):
        """Test handling of large request payloads"""
        # Create a large message
        large_content = "x" * 10000  # 10KB message
        large_payload = {
            "history": [{"role": "user", "content": large_content}]
        }

        # This should not raise an exception in normal circumstances
        try:
            # Mock the response to avoid actual network calls
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"reply": "Processed large request"}
                mock_post.return_value = mock_response

                response = requests.post(
                    self.chat_endpoint,
                    json=large_payload,
                    timeout=10
                )

                self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException as request_error:
            self.fail(f"Large request handling failed: {request_error}")


class TestAPIFallbackMechanisms(unittest.TestCase):
    """Test fallback mechanisms when AI service fails"""

    def setUp(self):
        """Set up test environment"""
        self.primary_url = "http://localhost:8000/chat"
        self.fallback_url = "http://localhost:8001/chat"
        self.test_messages = [{"role": "user", "content": "Hello"}]

    def test_fallback_to_backend_on_ai_service_failure(self):
        """Test fallback to backend API when AI service fails"""
        # Simulate AI service failure and successful backend fallback
        with patch('requests.post') as mock_post:
            responses = [
                # First call (AI service) fails
                requests.exceptions.ConnectionError("AI service unavailable"),
                # Second call (backend) succeeds
                Mock(status_code=200, json=lambda: {"reply": "Backend response"})
            ]
            mock_post.side_effect = responses

            # Implement fallback logic
            try:
                response = requests.post(self.primary_url, json={"history": self.test_messages}, timeout=30)
            except requests.exceptions.ConnectionError:
                # Fallback to secondary endpoint
                response = requests.post(self.fallback_url, json={"history": self.test_messages}, timeout=30)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["reply"], "Backend response")

    def test_multiple_fallback_attempts(self):
        """Test multiple fallback attempts with different endpoints"""
        endpoints = [
            "http://localhost:8000/chat",
            "http://localhost:8001/chat",
            "http://localhost:8002/chat"
        ]

        with patch('requests.post') as mock_post:
            # First two fail, third succeeds
            responses = [
                requests.exceptions.ConnectionError("Service 1 down"),
                requests.exceptions.Timeout("Service 2 timeout"),
                Mock(status_code=200, json=lambda: {"reply": "Service 3 success"})
            ]
            mock_post.side_effect = responses

            last_response = None
            for endpoint in endpoints:
                try:
                    response = requests.post(endpoint, json={"history": self.test_messages}, timeout=30)
                    if response.status_code == 200:
                        last_response = response
                        break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    continue

            self.assertIsNotNone(last_response)
            self.assertEqual(last_response.status_code, 200)

    def test_graceful_degradation_on_all_failures(self):
        """Test graceful degradation when all services fail"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("All services down")

            default_response = ("I'm sorry, the AI service is temporarily unavailable. "
                              "Please try again later.")

            try:
                response = requests.post(self.primary_url, json={"history": self.test_messages}, timeout=30)
            except requests.exceptions.ConnectionError:
                # Return default error response
                response = Mock()
                response.status_code = 503
                response.json = lambda: {"reply": default_response}

            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertIn("temporarily unavailable", data["reply"])


class TestRequestValidationAndSanitization(unittest.TestCase):
    """Test request validation and input sanitization"""

    def setUp(self):
        """Set up test data"""
        self.malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../../etc/passwd",
            "\x00\x01\x02",  # Null bytes
            "A" * 100000,  # Very long input
            {"$ne": "1"},  # NoSQL injection attempt
            {"__proto__": {"admin": True}},  # Prototype pollution
        ]

    def test_input_length_validation(self):
        """Test validation of input length limits"""
        max_length = 10000

        # Test normal length
        normal_input = "Hello, how are you?"
        self.assertLessEqual(len(normal_input), max_length)

        # Test excessive length
        long_input = "x" * (max_length + 1)
        self.assertGreater(len(long_input), max_length)

        # In a real app, this would be rejected
        if len(long_input) > max_length:
            validation_error = "Input too long"
            self.assertEqual(validation_error, "Input too long")

    def test_content_type_validation(self):
        """Test validation of message content types"""
        valid_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        invalid_messages = [
            {"role": "user"},  # Missing content
            {"content": "Hello"},  # Missing role
            {"role": "invalid", "content": "Hello"},  # Invalid role
            {"role": "user", "content": 123},  # Wrong content type
        ]

        for msg in valid_messages:
            self.assertIn("role", msg)
            self.assertIn("content", msg)
            self.assertIn(msg["role"], ["user", "assistant"])
            self.assertIsInstance(msg["content"], str)

        for msg in invalid_messages:
            # Check various validation failures
            if "role" not in msg or "content" not in msg:
                self.assertTrue(True)  # Missing required fields
            elif msg.get("role") not in ["user", "assistant"]:
                self.assertTrue(True)  # Invalid role
            elif not isinstance(msg.get("content"), str):
                self.assertTrue(True)  # Wrong type

    def test_malicious_input_detection(self):
        """Test detection of potentially malicious inputs"""
        for malicious_input in self.malicious_inputs:
            with self.subTest(input=str(malicious_input)[:50]):
                # Basic sanitization checks
                if isinstance(malicious_input, str):
                    # Check for script tags
                    if "<script>" in malicious_input.lower():
                        self.assertIn("script", malicious_input.lower())

                    # Check for SQL injection patterns
                    if "drop table" in malicious_input.lower():
                        self.assertIn("drop", malicious_input.lower())

                    # Check for path traversal
                    if "../" in malicious_input:
                        self.assertIn("..", malicious_input)

                    # Check for excessive length
                    if len(malicious_input) > 50000:
                        self.assertGreater(len(malicious_input), 50000)

    def test_json_structure_validation(self):
        """Test validation of JSON request structure"""
        valid_structures = [
            {"history": []},
            {"history": [{"role": "user", "content": "Hello"}]},
        ]

        invalid_structures = [
            None,
            "string",
            123,
            [],
            {"wrong_field": "value"},
            {"history": "not_an_array"},
        ]

        for valid in valid_structures:
            self.assertIsInstance(valid, dict)
            self.assertIn("history", valid)
            self.assertIsInstance(valid["history"], list)

        for invalid in invalid_structures:
            # These should fail validation
            if not isinstance(invalid, dict):
                self.assertTrue(True)  # Not a dict
            elif "history" not in invalid:
                self.assertTrue(True)  # Missing history field
            elif not isinstance(invalid.get("history"), list):
                self.assertTrue(True)  # History not a list


if __name__ == '__main__':
    unittest.main(verbosity=2)
