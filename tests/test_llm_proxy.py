import unittest
from unittest.mock import patch, Mock
from services.llm_proxy import LLMProxy


class TestLLMProxy(unittest.TestCase):
    @patch("services.llm_proxy.requests.post")
    def test_timeout(self, mock_post):
        mock_post.side_effect = Exception("Timeout")
        proxy = LLMProxy("fake_key")
        result = proxy.send_message("Hello")
        self.assertIn("error", result.lower())

    @patch("services.llm_proxy.requests.post")
    def test_http_error(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTPError")
        mock_post.return_value = mock_response
        proxy = LLMProxy("fake_key")
        result = proxy.send_message("Hello")
        self.assertIn("error", result.lower())

    @patch("services.llm_proxy.requests.post")
    def test_network_error(self, mock_post):
        mock_post.side_effect = Exception("NetworkError")
        proxy = LLMProxy("fake_key")
        result = proxy.send_message("Hello")
        self.assertIn("error", result.lower())

    @patch("services.llm_proxy.requests.post")
    def test_successful_response(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Gemini reply"}]}}]
        }
        mock_post.return_value = mock_response
        proxy = LLMProxy("fake_key")
        result = proxy.send_message("Hello")
        self.assertEqual(result, "Gemini reply")


if __name__ == "__main__":
    unittest.main()
