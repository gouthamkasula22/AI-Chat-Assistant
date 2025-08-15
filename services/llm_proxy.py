import requests
from utils.error_handler import handle_api_error

class LLMProxy:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def send_message(self, history: list) -> str:
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
                    "parts": [{"text": msg["content"]}]
                }
                for msg in filtered_history
            ]
        }
        
        # API request
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        
        try:
            response = requests.post(url, headers=headers, params=params, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.Timeout):
                user_message = "Request timed out. Please try again later."
            elif isinstance(e, requests.exceptions.HTTPError):
                user_message = f"HTTP error: {e.response.status_code} - {e.response.reason}"
            else:
                user_message = "Network error occurred. Please check your connection."
            return handle_api_error(e, user_message)
        
        except Exception as e:
            return handle_api_error(e, "An unexpected error occurred.")
