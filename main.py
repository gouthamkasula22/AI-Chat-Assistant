"""
AI Chat Assistant - Streamlit Frontend Application

This module provides a web-based chat interface for interacting with an AI assistant.
It includes session persistence, response time tracking, database-backed chat history,
and a clean user interface.
"""

import json
import os
import time
from typing import Dict, Any, Optional, List
import requests

import uuid
import streamlit as st
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import our new chat history service
from services.chat_history_service import ChatHistoryService
from services.advanced_ai_service import AdvancedAIService, ConversationStyle
from database.feedback_manager import FeedbackManager
from components.feedback_ui import FeedbackUI

# Import our logging system
from utils.logger import get_logger, log_user_interaction, log_performance, log_security_event

# Initialize logger
logger = get_logger('main_app')

st.set_page_config(page_title="AI Chat Assistant", page_icon="💬", layout="centered")

# Initialize chat history service
@st.cache_resource
def get_chat_history_service():
    """Initialize and cache the chat history service."""
    return ChatHistoryService()

# Initialize advanced AI service
@st.cache_resource
def get_advanced_ai_service():
    """Initialize and cache the advanced AI service."""
    return AdvancedAIService()


def get_browser_session_id() -> str:
    """
    Generate a consistent session ID that persists across browser refreshes.

    Returns:
        str: A unique session identifier
    """
    if "browser_session_id" not in st.session_state:
        st.session_state.browser_session_id = str(uuid.uuid4())
    return st.session_state.browser_session_id


def save_session_data() -> None:
    """Save session data to a temporary file for persistence."""
    try:
        session_id = get_browser_session_id()
        session_file = f"temp_session_{session_id}.json"

        session_data = {
            "messages": st.session_state.messages,
            "message_count": st.session_state.message_count,
            "conversation_started": st.session_state.conversation_started,
            "response_times": st.session_state.response_times,
            "total_response_time": st.session_state.total_response_time,
            "session_id": st.session_state.session_id,
        }

        with open(session_file, "w", encoding="utf-8") as session_file_handle:
            json.dump(session_data, session_file_handle)
    except (IOError, OSError, json.JSONEncodeError):
        pass  # Silent fail if can't save


def load_session_data() -> bool:
    """
    Load session data from temporary file.

    Returns:
        bool: True if session data was successfully loaded, False otherwise
    """
    try:
        session_id = get_browser_session_id()
        session_file = f"temp_session_{session_id}.json"

        if os.path.exists(session_file):
            with open(session_file, "r", encoding="utf-8") as session_file_handle:
                session_data = json.load(session_file_handle)

            # Restore session state
            st.session_state.messages = session_data.get("messages", [])
            st.session_state.message_count = session_data.get("message_count", 0)
            st.session_state.conversation_started = session_data.get("conversation_started", False)
            st.session_state.response_times = session_data.get("response_times", [])
            st.session_state.total_response_time = session_data.get("total_response_time", 0)
            st.session_state.session_id = session_data.get("session_id", get_browser_session_id())
            return True
    except (IOError, OSError, json.JSONDecodeError):
        pass  # Silent fail if can't load
    return False


# Custom CSS for clean, professional look
st.markdown(
    """
<style>
/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main styling */
.stApp {
    background: #000000;
}

/* Title styling */
.main-title {
    text-align: center;
    color: #ffffff;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.subtitle {
    text-align: center;
    color: #cccccc;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* Chat messages */
.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 25px 25px 8px 25px;
    margin: 0.8rem 0 0.8rem 15%;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    font-size: 1.1rem;
    line-height: 1.5;
}

.assistant-message {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    color: #ecf0f1;
    padding: 1rem 1.5rem;
    border-radius: 25px 25px 25px 8px;
    margin: 0.8rem 15% 0.8rem 0;
    box-shadow: 0 4px 15px rgba(44, 62, 80, 0.3);
    border: 1px solid #4a5568;
    font-size: 1.1rem;
    line-height: 1.5;
}

/* Input styling */
.input-container {
    position: relative;
    margin-top: 1rem;
}

.stTextInput > div > div > input {
    border-radius: 25px;
    border: 2px solid #4a5568;
    padding: 1rem 4rem 1rem 1.5rem;
    font-size: 1.1rem;
    background: #2d3748;
    color: #e2e8f0;
    width: 100%;
}

.stTextInput > div > div > input:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
    background: #2d3748;
}

.send-button {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 50%;
    width: 45px;
    height: 45px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    transition: all 0.3s ease;
}

.send-button:hover {
    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    transform: translateY(-50%) scale(1.1);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.send-icon {
    color: white;
    font-size: 1.2rem;
    margin-left: 2px;
}

.stButton {
    display: block !important;
    visibility: visible !important;
}

/* Force all buttons to be visible and clickable */
.stButton > button {
    color: white !important;
    visibility: visible !important;
    opacity: 1 !important;
    display: block !important;
    background-color: #4a5568 !important;
    border: 1px solid #667eea !important;
    cursor: pointer !important;
    pointer-events: auto !important;
}

/* Clear button specific styling */
div[data-testid="column"]:nth-child(3) .stButton button {
    background: #dc3545 !important;
    color: white !important;
    visibility: visible !important;
    opacity: 1 !important;
    display: block !important;
    cursor: pointer !important;
    pointer-events: auto !important;
    border: 2px solid #dc3545 !important;
    border-radius: 8px !important;
    padding: 0.6rem 1rem !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
}

/* Stats button specific styling */
div[data-testid="column"]:nth-child(2) .stButton button {
    background: #667eea !important;
    color: white !important;
    visibility: visible !important;
    opacity: 1 !important;
    display: block !important;
    cursor: pointer !important;
    pointer-events: auto !important;
    border: 2px solid #667eea !important;
    border-radius: 8px !important;
    padding: 0.6rem 1rem !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
}

/* Clear button styling */
.stButton > button[kind="secondary"] {
    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
    color: white !important;
    border: 2px solid #dc3545 !important;
    border-radius: 8px !important;
    padding: 0.6rem 1rem !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 3px 10px rgba(220, 53, 69, 0.3) !important;
}

.stButton > button[kind="secondary"]:hover {
    background: linear-gradient(135deg, #c82333 0%, #a71e2a 100%) !important;
    border-color: #c82333 !important;
    box-shadow: 0 5px 15px rgba(220, 53, 69, 0.5) !important;
    transform: translateY(-2px) !important;
}

.stButton > button[kind="secondary"]:focus {
    background: linear-gradient(135deg, #c82333 0%, #a71e2a 100%) !important;
    border-color: #dc3545 !important;
    box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.3) !important;
}

/* Stats button styling */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: 2px solid #667eea !important;
    border-radius: 8px !important;
    padding: 0.6rem 1rem !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
    border-color: #5a67d8 !important;
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.5) !important;
    transform: translateY(-2px) !important;
}

/* General button visibility fix */
.stButton > button {
    color: white !important;
    visibility: visible !important;
    opacity: 1 !important;
    display: block !important;
    background-color: #4a5568 !important;
    border: 1px solid #667eea !important;
}

/* Extra visibility rules for buttons */
button[data-testid="baseButton-primary"],
button[data-testid="baseButton-secondary"],
div[data-testid="stButton"] button {
    visibility: visible !important;
    opacity: 1 !important;
    display: flex !important;
    background: #dc3545 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1rem !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    align-items: center;
    justify-content: center;
    min-height: 38px;
    cursor: pointer;
}

/* Specific clear button targeting */
div[data-testid="column"]:nth-child(3) button {
    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
    color: white !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Stats button targeting */
div[data-testid="column"]:nth-child(2) button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    visibility: visible !important;
    opacity: 1 !important;
}
    display: block !important;
}

/* Response time */
.response-time {
    text-align: center;
    color: #a0aec0;
    font-size: 1rem;
    margin-top: 1rem;
    background: #2d3748;
    padding: 0.5rem 1rem;
    border-radius: 15px;
    border: 1px solid #4a5568;
    display: inline-block;
    width: 100%;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* Sidebar styling */
.css-1d391kg {
    background: #1a202c !important;
}

.sidebar .stMarkdown {
    color: #e2e8f0 !important;
}

.sidebar .stButton > button {
    background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%) !important;
    color: white !important;
    border: 1px solid #4a5568 !important;
    border-radius: 8px !important;
    margin-bottom: 0.5rem !important;
    font-size: 0.9rem !important;
    padding: 0.5rem !important;
    transition: all 0.3s ease !important;
}

.sidebar .stButton > button:hover {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border-color: #667eea !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
}

/* New Chat button special styling */
.sidebar .stButton:first-child > button {
    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%) !important;
    border-color: #48bb78 !important;
    font-weight: 600 !important;
}

.sidebar .stButton:first-child > button:hover {
    background: linear-gradient(135deg, #68d391 0%, #48bb78 100%) !important;
}

/* Sidebar metrics styling */
.sidebar .metric-container {
    background: #2d3748 !important;
    border: 1px solid #4a5568 !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
    margin: 0.25rem 0 !important;
}

/* Inline AI selector styling */
.stSelectbox > div > div {
    background: #2d3748 !important;
    border: 1px solid #4a5568 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

.stSelectbox > div > div > div {
    color: #e2e8f0 !important;
}

.stSelectbox label {
    color: #a0aec0 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    margin-bottom: 0.25rem !important;
}

/* Input container styling */
.input-container .stSelectbox {
    margin-bottom: 1rem !important;
}

/* Clean selectbox dropdown */
.stSelectbox > div > div[data-baseweb="select"] > div {
    background: #2d3748 !important;
    border: 1px solid #4a5568 !important;
    color: #e2e8f0 !important;
}

/* Selectbox options */
.stSelectbox > div > div[data-baseweb="select"] > div > div {
    background: #2d3748 !important;
    color: #e2e8f0 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# Title and subtitle
st.markdown('<h1 class="main-title">💬 AI Chat Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Powered by Google Gemini AI</p>', unsafe_allow_html=True)

# Current conversation indicator
try:
    current_conversation = st.session_state.chat_service.db_manager.get_conversation_by_session(
        st.session_state.session_id
    )
    if current_conversation and st.session_state.messages:
        # Get current AI model and style
        current_model = getattr(st.session_state, 'selected_ai_model', 'Auto')
        current_style = getattr(st.session_state, 'selected_style', 'helpful')

        st.markdown(
            f'<div style="text-align: center; color: #a0aec0; margin-bottom: 1rem; font-size: 0.9rem;">'
            f'📝 <strong>{current_conversation["title"]}</strong> • '
            f'🤖 {current_model} • 🎭 {current_style.title()} • '
            f'💬 {current_conversation["total_messages"]} messages</div>',
            unsafe_allow_html=True
        )
    elif hasattr(st.session_state, 'selected_ai_model') and st.session_state.selected_ai_model:
        # Show model info even for new conversations
        current_model = st.session_state.selected_ai_model
        current_style = getattr(st.session_state, 'selected_style', 'helpful')
        st.markdown(
            f'<div style="text-align: center; color: #a0aec0; margin-bottom: 1rem; font-size: 0.9rem;">'
            f'🤖 {current_model} • 🎭 {current_style.title()}</div>',
            unsafe_allow_html=True
        )
except:
    pass  # Silent fail if conversation info can't be loaded


# Initialize persistent session state
def initialize_session_state():
    """Initialize session state with database-backed conversation data."""

    # Create a unique session key that persists across refreshes
    if "session_key" not in st.session_state:
        st.session_state.session_key = get_browser_session_id()

    # Initialize our chat history service
    if "chat_service" not in st.session_state:
        st.session_state.chat_service = get_chat_history_service()

    # Initialize our advanced AI service
    if "ai_service" not in st.session_state:
        st.session_state.ai_service = get_advanced_ai_service()

    # Initialize feedback UI using the AI service's feedback manager
    if "feedback_ui" not in st.session_state:
        st.session_state.feedback_ui = FeedbackUI(st.session_state.ai_service.feedback_manager)

    # Initialize session ID
    if "session_id" not in st.session_state:
        st.session_state.session_id = st.session_state.session_key

    # Try to load existing session data first
    session_loaded = load_session_data()

    # Load conversation history from database if not loaded from session
    if "messages" not in st.session_state or not session_loaded:
        # Get conversation history from database
        history = st.session_state.chat_service.get_conversation_history(
            session_id=st.session_state.session_id
        )

        # Convert database format to Streamlit format
        st.session_state.messages = []
        for msg in history:
            st.session_state.messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Calculate statistics from loaded history
        st.session_state.message_count = len(st.session_state.messages)
        st.session_state.conversation_started = len(st.session_state.messages) > 0

    # Initialize other session state variables
    if "last_input" not in st.session_state:
        st.session_state.last_input = None
    if "last_response_time" not in st.session_state:
        st.session_state.last_response_time = None
    if "total_response_time" not in st.session_state:
        st.session_state.total_response_time = 0
    if "response_times" not in st.session_state:
        st.session_state.response_times = []

    # Initialize AI configuration
    if "selected_ai_model" not in st.session_state:
        st.session_state.selected_ai_model = None
    if "selected_style" not in st.session_state:
        st.session_state.selected_style = "helpful"
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7

    # Migration: Check for old session files and import them
    if "migration_checked" not in st.session_state:
        try:
            migrated = st.session_state.chat_service.migrate_from_session_files()
            if migrated > 0:
                st.success(f"📥 Migrated {migrated} conversation(s) from previous sessions!")
                # Reload messages after migration
                history = st.session_state.chat_service.get_conversation_history(
                    session_id=st.session_state.session_id
                )
                st.session_state.messages = []
                for msg in history:
                    st.session_state.messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                st.session_state.message_count = len(st.session_state.messages)
        except Exception as error:
            # Silent migration failure - don't disrupt user experience
            pass
        finally:
            st.session_state.migration_checked = True


# Initialize session state
initialize_session_state()

# Chat History Sidebar
with st.sidebar:
    st.markdown("### 💬 Chat History")

    # New Chat button
    if st.button("➕ New Chat", use_container_width=True):
        try:
            # Clear current session state
            st.session_state.clear()
            # Generate new session ID
            new_session_id = str(uuid.uuid4())
            st.session_state.session_key = new_session_id
            st.session_state.session_id = new_session_id
            # Reinitialize
            initialize_session_state()
            st.success("🆕 Started new chat!")
            st.rerun()
        except Exception as error:
            st.error(f"Error starting new chat: {str(e)}")

    st.markdown("---")

    # Show recent conversations
    try:
        recent_conversations = st.session_state.chat_service.get_recent_conversations(limit=10)

        if recent_conversations:
            st.markdown("**Recent Conversations:**")

            for conv in recent_conversations:
                # Create a shorter display title
                display_title = conv['title']
                if len(display_title) > 30:
                    display_title = display_title[:27] + "..."

                # Show conversation info
                created_date = conv['created_at'][:10]  # Just the date part
                message_count = conv['total_messages']

                # Check if this is the current conversation
                is_current = conv['session_id'] == st.session_state.session_id

                # Create a container for each conversation
                with st.container():
                    if is_current:
                        st.markdown(f"**🔹 {display_title}**")
                        st.caption(f"📅 {created_date} • 💬 {message_count} messages (Current)")
                    else:
                        # Button to switch to this conversation
                        if st.button(f"💬 {display_title}", key=f"conv_{conv['id']}", use_container_width=True):
                            try:
                                # Switch to this conversation
                                st.session_state.session_id = conv['session_id']
                                st.session_state.session_key = conv['session_id']

                                # Load conversation history
                                history = st.session_state.chat_service.get_conversation_history(
                                    session_id=conv['session_id']
                                )

                                # Update session state
                                st.session_state.messages = []
                                for msg in history:
                                    st.session_state.messages.append({
                                        "role": msg["role"],
                                        "content": msg["content"]
                                    })

                                st.session_state.message_count = len(st.session_state.messages)
                                st.session_state.conversation_started = len(st.session_state.messages) > 0

                                st.success(f"📂 Loaded conversation: {conv['title']}")
                                st.rerun()

                            except Exception as error:
                                st.error(f"Error loading conversation: {str(e)}")

                        st.caption(f"📅 {created_date} • 💬 {message_count} messages")

                st.markdown("")  # Add some spacing
        else:
            st.info("No previous conversations found.")

    except Exception as error:
        st.error(f"Error loading chat history: {str(e)}")

    # Database Statistics (collapsible)
    with st.expander("📊 Database Stats"):
        try:
            stats = st.session_state.chat_service.get_service_stats()
            db_stats = stats['database_stats']

            st.metric("Total Conversations", db_stats['conversations'])
            st.metric("Total Messages", db_stats['messages'])

            # Database size in a readable format
            db_size_kb = db_stats['db_size_bytes'] / 1024
            if db_size_kb < 1024:
                size_display = f"{db_size_kb:.1f} KB"
            else:
                size_display = f"{db_size_kb/1024:.1f} MB"
            st.metric("Database Size", size_display)

            st.caption(f"Service Status: {stats['service_status']}")

        except Exception as error:
            st.error(f"Error loading stats: {str(e)}")

    # AI Advanced Settings
    with st.expander("⚙️ Advanced Settings"):
        try:
            # Temperature control
            temperature = st.slider(
                "Response Creativity",
                min_value=0.1,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher values = more creative/random responses"
            )
            st.session_state.temperature = temperature

            # Model testing
            if st.button("🧪 Test AI Models", use_container_width=True):
                with st.spinner("Testing AI models..."):
                    test_results = st.session_state.ai_service.test_model_connectivity()

                    for model_name, result in test_results.items():
                        status = "✅" if result['is_available'] else "❌"
                        st.caption(f"{status} {model_name}: {result.get('error_message', 'OK')}")

        except Exception as error:
            st.error(f"Error loading AI settings: {str(e)}")

    # AI Analytics Dashboard
    with st.expander("📈 AI Analytics"):
        try:
            analytics = st.session_state.ai_service.get_service_analytics()

            # Usage metrics
            st.subheader("Usage Statistics")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Total Requests", analytics['usage_analytics']['total_requests'])
                st.metric("Success Rate", f"{analytics['success_rate_percentage']}%")

            with col2:
                st.metric("Successful", analytics['usage_analytics']['successful_requests'])
                st.metric("Failed", analytics['usage_analytics']['failed_requests'])

            # Average response time
            avg_time = analytics['usage_analytics']['average_response_time']
            st.metric("Avg Response Time", f"{avg_time:.2f}s")

            # Model usage breakdown
            if analytics['usage_analytics']['model_usage']:
                st.subheader("Model Usage")
                for model, count in analytics['usage_analytics']['model_usage'].items():
                    st.caption(f"🤖 {model}: {count} requests")

            # Style usage breakdown
            if analytics['usage_analytics']['style_usage']:
                st.subheader("Style Usage")
                for style, count in analytics['usage_analytics']['style_usage'].items():
                    st.caption(f"🎭 {style.title()}: {count} requests")

            # System health
            st.subheader("System Health")
            health = analytics['service_health']
            health_color = "🟢" if health == "healthy" else "🟡"
            st.caption(f"{health_color} Status: {health.title()}")

            # Model system status
            model_status = analytics['model_system_status']
            available_models = sum(1 for model in model_status['models'].values()
                                 if model['is_available'] and model['within_rate_limit'])
            st.caption(f"🤖 Available Models: {available_models}/{model_status['total_models']}")

        except Exception as error:
            st.error(f"Error loading analytics: {str(e)}")

    # Feedback & Learning Analytics
    with st.expander("🧠 Learning Analytics"):
        try:
            learning_insights = st.session_state.ai_service.get_learning_insights()

            if 'error' not in learning_insights:
                insights = learning_insights.get('learning_insights', {})

                # Model recommendations
                if 'model_recommendations' in learning_insights:
                    st.subheader("📊 Model Recommendations")
                    recommendations = learning_insights['model_recommendations']
                    for style, model in recommendations.items():
                        st.caption(f"🎭 {style.title()}: {model}")

                # Feedback statistics
                if 'total_feedback' in insights:
                    st.subheader("💬 Feedback Summary")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Total Feedback", insights.get('total_feedback', 0))
                        st.metric("Avg Rating", f"{insights.get('average_rating', 0):.1f}/5")

                    with col2:
                        st.metric("Positive Feedback", insights.get('positive_feedback_count', 0))
                        st.metric("Learning Score", f"{insights.get('learning_effectiveness', 0):.1f}%")

                # Top performing models
                if 'top_models' in insights:
                    st.subheader("🏆 Top Models")
                    for model in insights['top_models'][:3]:
                        st.caption(f"🤖 {model['model_name']}: {model['avg_rating']:.1f}⭐")

                # Recent improvements
                if 'recent_improvements' in insights:
                    improvements = insights['recent_improvements']
                    if improvements:
                        st.subheader("📈 Recent Improvements")
                        for improvement in improvements[:3]:
                            st.caption(f"✨ {improvement}")
            else:
                st.info("📊 Learning analytics will appear after feedback is collected.")

        except Exception as error:
            st.error(f"Error loading learning analytics: {str(e)}")

# Enhanced clear chat button layout
col1, col2 = st.columns([4, 1])

# Remove the statistics box - we'll show response times with each message instead

# Force button visibility with additional CSS
st.markdown(
    """
<style>
/* Override any hiding CSS for buttons */
.stButton, .stButton > button {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
}

/* Make sure clear buttons are always visible */
div[data-testid="column"] .stButton button {
    background: #dc3545 !important;
    color: white !important;
    border: none !important;
    padding: 8px 16px !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    font-weight: bold !important;
}
</style>
""",
    unsafe_allow_html=True,
)

with col1:
    # Empty space for cleaner layout
    pass

with col2:
    if st.session_state.messages:
        # Database-aware clear chat button
        if st.button("🗑️ Clear Chat", key="clear_simple"):
            try:
                # Get the current conversation ID before clearing
                conversation = st.session_state.chat_service.db_manager.get_conversation_by_session(
                    st.session_state.session_id
                )

                if conversation:
                    # Delete the conversation from database (cascades to messages)
                    st.session_state.chat_service.delete_conversation(conversation['id'])

                # Clear session state
                st.session_state.clear()

                # Reinitialize with new session
                initialize_session_state()

                st.success("✅ Chat cleared successfully!")
                st.rerun()

            except Exception as error:
                st.error(f"❌ Error clearing chat: {str(e)}")
                # Fallback: clear session state anyway
                st.session_state.clear()
                initialize_session_state()
                st.rerun()

# Display chat messages with response times below each AI response
response_index = 0  # Track AI response index separately
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.markdown(
            f"""
        <div class="user-message">
            <strong>You:</strong><br>
            {message["content"]}
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        # AI response with response time below
        st.markdown(
            f"""
        <div class="assistant-message">
            <strong>AI Assistant:</strong><br>
            {message["content"]}
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Show response time for this specific response if available
        if hasattr(st.session_state, "response_times") and response_index < len(
            st.session_state.response_times
        ):
            response_time = st.session_state.response_times[response_index]
            st.markdown(
                f"""
            <div style="text-align: right; margin: 0.5rem 15% 1rem 0;">
                <small style="color: #10b981; background: rgba(16, 185, 129, 0.1);
                              padding: 0.3rem 0.8rem; border-radius: 10px;
                              border: 1px solid rgba(16, 185, 129, 0.3);">
                    ⚡ Response time: {response_time:.1f}s
                </small>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Add feedback UI for AI responses
        if hasattr(st.session_state, 'feedback_ui'):
            # Generate unique message ID using index, content, and timestamp
            import time
            message_id = abs(hash(f"{i}_{message['content'][:100]}_{time.time()}")) % 1000000
            conversation_id = abs(hash(st.session_state.session_id)) % 10000

            # Render feedback UI
            st.session_state.feedback_ui.render_message_feedback(
                message_id=message_id,
                conversation_id=conversation_id,
                ai_model_used="gemini-pro",  # Default model
                conversation_style="helpful",  # Default style
                response_time=1.0,  # Default response time
                session_id=st.session_state.session_id
            )

        response_index += 1  # Increment for next AI response

# Input form with AI model selection
st.markdown('<div class="input-container">', unsafe_allow_html=True)
with st.form(key="chat_form", clear_on_submit=True):
    # AI Model & Style selector in compact row
    col_model, col_style, col_spacer = st.columns([2, 2, 6])

    with col_model:
        # Get available models
        try:
            available_models = st.session_state.ai_service.get_available_models()
            model_options = []
            model_names = []

            for model in available_models:
                # Create more distinct shortened names
                name = model['name']
                if 'DialoGPT Large' in name:
                    short_name = 'DialoGPT-L'
                elif 'DialoGPT Medium' in name:
                    short_name = 'DialoGPT-M'
                elif 'BlenderBot 400M' in name:
                    short_name = 'BlenderBot'
                elif 'Gemini Pro' in name:
                    short_name = 'Gemini Pro'
                else:
                    # Fallback: remove common suffixes
                    short_name = name.replace(' Large', '').replace(' Medium', '').replace(' 400M', '')

                model_options.append(short_name)
                model_names.append(model['name'])

            if model_options:
                # Find the index of the currently selected model
                current_model = getattr(st.session_state, 'selected_ai_model', None)
                default_idx = 0
                if current_model and current_model in model_names:
                    default_idx = model_names.index(current_model)

                selected_model_idx = st.selectbox(
                    "Model",
                    range(len(model_options)),
                    format_func=lambda x: model_options[x],
                    index=default_idx,
                    key="inline_model_selection",
                    help="AI Model"
                )

                if model_names:
                    st.session_state.selected_ai_model = model_names[selected_model_idx]
            else:
                st.warning("No models")

        except Exception as error:
            st.error(f"Model error: {str(e)}")

    with col_style:
        # Conversation style selector
        try:
            available_styles = st.session_state.ai_service.get_conversation_styles()
            style_options = list(available_styles.keys())
            # Shortened style names for compact display
            style_short_names = {
                'friendly': 'Friendly',
                'professional': 'Professional',
                'creative': 'Creative',
                'analytical': 'Analytical',
                'casual': 'Casual',
                'helpful': 'Helpful'
            }

            # Find the index of the currently selected style
            current_style = getattr(st.session_state, 'selected_style', 'helpful')
            default_style_idx = 5  # Default to "helpful"
            if current_style and current_style in style_options:
                default_style_idx = style_options.index(current_style)

            selected_style_idx = st.selectbox(
                "Style",
                range(len(style_options)),
                format_func=lambda x: style_short_names.get(style_options[x], style_options[x].title()),
                index=default_style_idx,
                key="inline_style_selection",
                help="Conversation Style"
            )

            st.session_state.selected_style = style_options[selected_style_idx]

        except Exception as error:
            st.error(f"Style error: {str(e)}")

    # Message input row
    col1, col2 = st.columns([10, 1])
    with col1:
        user_input = st.text_input(
            "Type your message:",
            placeholder="Ask me anything...",
            key="user_input",
            label_visibility="collapsed",
        )
    with col2:
        submitted = st.form_submit_button("➤", help="Send message")

st.markdown(
    """
<script>
document.addEventListener('DOMContentLoaded', function() {
    const sendButton = document.querySelector('[data-testid="stButton"] button');
    const inputField = document.querySelector('input[type="text"]');

    if (sendButton && inputField) {
        sendButton.style.cssText = `
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 50%;
            width: 45px;
            height: 45px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            color: white;
            font-size: 1.2rem;
        `;
    }
});
</script>
""",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)


# Enhanced input validation
def validate_input(text):
    """Enhanced input validation with detailed feedback"""
    if not text or not text.strip():
        return False, "Please enter a message."

    text = text.strip()

    if len(text) < 2:
        return False, "Message too short (minimum 2 characters)."

    if len(text) > 500:
        return False, "Message too long (maximum 500 characters)."

    # Check for potentially harmful content
    harmful_patterns = ["<script", "javascript:", "onload=", "onerror="]
    if any(pattern in text.lower() for pattern in harmful_patterns):
        return False, "Invalid characters detected."

    # Check for spam (repeated characters)
    if any(char * 10 in text for char in "abcdefghijklmnopqrstuvwxyz"):
        return False, "Please avoid repeated characters."

    return True, text


def get_ai_response(messages, session_id):
    """Enhanced AI response using Advanced AI Service with multiple models and styles"""
    try:
        # Get user preferences from session state
        preferred_model = getattr(st.session_state, 'selected_ai_model', None)
        conversation_style = getattr(st.session_state, 'selected_style', 'helpful')
        temperature = getattr(st.session_state, 'temperature', 0.7)

        # Convert style string to enum
        style_enum = ConversationStyle(conversation_style)

        # Use advanced AI service to generate response
        response = st.session_state.ai_service.generate_response(
            messages=messages,
            session_id=session_id,
            style=style_enum,
            preferred_model=preferred_model,
            temperature=temperature
        )

        if response.success:
            return True, response.content
                    # Try fallback to backend API if advanced AI fails
            try:
                fallback_response = requests.post(
                    "http://localhost:8000/chat",
                    json={"history": messages, "session_id": session_id},
                    timeout=30,
                    headers={"Content-Type": "application/json"},
                )

                if fallback_response.status_code == 200:
                    data = fallback_response.json()
                    reply = data.get("reply", "").strip()
                    if reply:
                        return True, reply
            except:
                pass  # Fallback failed, use original error

            return False, response.error_message or "AI service failed to generate response"

    except Exception as error:
        # Final fallback to original backend
        try:
            response = requests.post(
                "http://localhost:8000/chat",
                json={"history": messages, "session_id": session_id},
                timeout=30,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "").strip()

                if not reply:
                    return False, "Received empty response from AI."

                return True, reply

            elif response.status_code == 429:
                return False, "⚠️ Rate limit exceeded. Please wait before sending another message."
            elif response.status_code == 500:
                return False, "🔧 Server is experiencing issues. Please try again in a moment."
            else:
                return False, f"❌ Server responded with status {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "⏱️ Request timed out. The AI is taking longer than usual."
        except requests.exceptions.ConnectionError:
            return False, "🔌 Cannot connect to the AI server. Please ensure the backend is running."
        except requests.exceptions.RequestException as error:
            return False, f"🌐 Network error: {str(error)}"
        except Exception as error:
            return False, f"❌ Unexpected error: {str(error)}"


# Handle message sending with enhanced features
if submitted and user_input:
    # Log user interaction
    log_user_interaction(
        session_id=st.session_state.session_id,
        action="message_submitted",
        input_length=len(user_input),
        conversation_started=st.session_state.conversation_started,
        message_count=st.session_state.message_count
    )

    # Validate input
    is_valid, result = validate_input(user_input)

    if not is_valid:
        st.error(result)
        log_security_event("invalid_input_blocked", {
            "session_id": st.session_state.session_id,
            "input": user_input[:100],  # Log first 100 chars only
            "validation_error": result
        })
    elif user_input != st.session_state.last_input:
        # Mark conversation as started
        if not st.session_state.conversation_started:
            st.session_state.conversation_started = True
            st.success("🚀 Conversation started!")
            log_user_interaction(
                session_id=st.session_state.session_id,
                action="conversation_started"
            )

        try:
            # Add user message to database and session state
            user_msg = st.session_state.chat_service.add_user_message(
                session_id=st.session_state.session_id,
                content=result
            )

            # Add to session state for immediate display
            st.session_state.messages.append({"role": "user", "content": result})
            st.session_state.last_input = user_input
            st.session_state.message_count += 1

            # Show typing indicator
            with st.spinner("🤖 AI is analyzing your message..."):
                start_time = time.time()

                # Get AI response
                success, ai_response = get_ai_response(
                    st.session_state.messages, st.session_state.session_id
                )

                elapsed = time.time() - start_time

                if success:
                    # Add assistant message to database
                    assistant_msg = st.session_state.chat_service.add_assistant_message(
                        session_id=st.session_state.session_id,
                        content=ai_response,
                        response_time=elapsed
                    )

                    # Add to session state for immediate display
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    st.session_state.message_count += 1
                    st.session_state.last_response_time = elapsed
                    st.session_state.total_response_time += elapsed

                    # Store individual response time
                    st.session_state.response_times.append(elapsed)

                    # Save session data to persist response times
                    save_session_data()

                    # Success notification
                    st.success(f"✅ Message delivered successfully!")

                else:
                    st.error(ai_response)
                    # Don't add failed responses to conversation history
                    st.session_state.messages.pop()  # Remove user message from session state
                    st.session_state.message_count -= 1

        except Exception as error:
            st.error(f"❌ Error saving message: {str(error)}")
            # Continue with in-memory operation as fallback
            st.session_state.messages.append({"role": "user", "content": result})
            st.session_state.last_input = user_input
            st.session_state.message_count += 1

        st.rerun()

# Welcome message for empty chat with clean, simple design
if not st.session_state.messages:
    st.markdown(
        """
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem; border-radius: 15px; margin: 1rem 0; text-align: center;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3); border: 1px solid #818cf8;">
        <h3 style="color: white; margin-bottom: 1rem;">👋 Welcome to AI Chat Assistant!</h3>
        <div style="color: #e2e8f0; font-size: 1.1rem; line-height: 1.6;">
            🎯 <strong>Clean & Simple Chat Experience:</strong><br>
            • Contextual conversations that remember your chat<br>
            • Persistent sessions across browser refreshes<br>
            • Real-time response time tracking<br>
            • Professional, clutter-free interface<br><br>
            💬 <strong>Ready to start?</strong> Type your message above!
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Simple session info display
    st.markdown(
        f"""
    <div style="background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
                padding: 1.5rem; border-radius: 12px; margin-top: 1rem;
                border: 1px solid #667eea; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);">
        <div style="color: #e2e8f0; text-align: center;">
            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">
                🔒 Session Active
            </div>
            <div style="color: #a0aec0; font-size: 0.95rem;">
                ID: <strong>{st.session_state.session_id[:16]}...</strong><br>
                Status: <span style="color: #10b981;">🟢 Ready & Persistent</span><br>
                <small>Your conversation will be saved during this browser session</small>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
