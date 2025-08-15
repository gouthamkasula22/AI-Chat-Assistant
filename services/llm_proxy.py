import requests
from utils.error_handler import handle_api_error

class LLMProxy:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def send_message(self, message: str) -> str:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {"parts": [{"text": message}]}
            ]
        }
        params = {"key": self.api_key}
        try:
            response = requests.post(url, headers=headers, params=params, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Gemini's response structure
            return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except requests.exceptions.RequestException as e:
        # Automated error message based on exception type
          if isinstance(e, requests.exceptions.Timeout):
            user_message = "Request timed out. Please try again later."
          elif isinstance(e, requests.exceptions.HTTPError):
            user_message = f"HTTP error: {e.response.status_code} - {e.response.reason}"
          else:
            user_message = "Network error occurred. Please check your connection."
          return handle_api_error(e, user_message)
        except Exception as e:
          return handle_api_error(e, "An unexpected error occurred.")