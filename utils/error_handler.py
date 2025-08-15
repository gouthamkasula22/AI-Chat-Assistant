import logging
import traceback
def handle_api_error(error: Exception, user_message: str = None) -> str:
    # Basic error handling logic
    logging.error(f"API Error: {error}")
    logging.error(traceback.format_exc())
    if user_message:
        return user_message
    return "An error occurred while processing your request. Please try again."