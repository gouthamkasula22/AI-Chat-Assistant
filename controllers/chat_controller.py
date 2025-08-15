from services.llm_proxy import LLMProxy
from config.config import Config

llm_proxy = LLMProxy(Config.GEMINI_API_KEY)

def get_llm_reply(message: str) -> str:
    return llm_proxy.send_message(message)