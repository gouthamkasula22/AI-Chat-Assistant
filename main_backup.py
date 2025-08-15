"""
AI Chat Assistant - Streamlit Frontend Application

This module provides a web-based chat interface for interacting with an AI assistant.
It includes session persistence, response time tracking, database-backed chat history,
and a clean user interface.
"""

import json
import os
import time
import uuid
from typing import Dict, Any, Optional, List

import requests
import streamlit as st

# Import our new chat history service
from services.chat_history_service import ChatHistoryService
# Import CSS loader utility
from utils.css_loader import init_styles

st.set_page_config(page_title="AI Chat Assistant", page_icon="💬", layout="centered")

# Initialize chat history service
@st.cache_resource
def get_chat_history_service():
    """Initialize and cache the chat history service."""
    return ChatHistoryService()


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


# Load external CSS styles
init_styles()

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

/* Essential Streamlit overrides only - detailed styles loaded from external CSS files */
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

/* Enhanced Sidebar Styling */
.css-1d391kg, .css-1lcbmhc, .css-1v3fvcr {
    background: linear-gradient(145deg, #1a202c 0%, #2d3748 100%) !important;
    border-right: 2px solid #4a5568 !important;
}

/* Sidebar content styling */
.sidebar .stMarkdown {
    color: #e2e8f0 !important;
}

.sidebar h3 {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    margin-bottom: 1rem !important;
    text-align: center !important;
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}

/* Enhanced New Chat Button */
.sidebar .stButton:first-child > button {
    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 1rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3) !important;
    transition: all 0.3s ease !important;
    cursor: pointer !important;
    text-transform: none !important;
}

.sidebar .stButton:first-child > button:hover {
    background: linear-gradient(135deg, #68d391 0%, #48bb78 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(72, 187, 120, 0.4) !important;
}

/* Conversation Cards */
.conversation-card {
    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%) !important;
    border: 1px solid #4a5568 !important;
    border-radius: 12px !important;
    padding: 0.75rem !important;
    margin: 0.5rem 0 !important;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.3s ease !important;
    cursor: pointer !important;
}

.conversation-card:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.2) !important;
    border-color: #667eea !important;
}

.conversation-card.current {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border-color: #667eea !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
}

/* Conversation Buttons */
.sidebar .stButton:not(:first-child) > button {
    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%) !important;
    color: #e2e8f0 !important;
    border: 1px solid #4a5568 !important;
    border-radius: 10px !important;
    padding: 0.6rem 0.8rem !important;
    margin: 0.3rem 0 !important;
    font-size: 0.9rem !important;
    width: 100% !important;
    text-align: left !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
}

.sidebar .stButton:not(:first-child) > button:hover {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border-color: #667eea !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    color: white !important;
}

/* Sidebar Divider */
.sidebar hr {
    border: none !important;
    height: 2px !important;
    background: linear-gradient(90deg, transparent, #4a5568, transparent) !important;
    margin: 1rem 0 !important;
}

/* Conversation Meta Info */
.conversation-meta {
    font-size: 0.75rem !important;
    color: #a0aec0 !important;
    margin-top: 0.25rem !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
}

.conversation-meta .date {
    opacity: 0.8 !important;
}

.conversation-meta .message-count {
    background: rgba(102, 126, 234, 0.2) !important;
    padding: 0.2rem 0.4rem !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}

/* Sidebar Stats */
.sidebar .stMetric {
    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%) !important;
    border: 1px solid #4a5568 !important;
    border-radius: 10px !important;
    padding: 0.75rem !important;
    margin: 0.3rem 0 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
}

.sidebar .stMetric label {
    color: #a0aec0 !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}

.sidebar .stMetric [data-testid="metric-value"] {
    color: #667eea !important;
    font-weight: 600 !important;
    font-size: 1.2rem !important;
}

/* Sidebar Expander */
.sidebar .streamlit-expanderHeader {
    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%) !important;
    border: 1px solid #4a5568 !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-weight: 500 !important;
}

.sidebar .streamlit-expanderContent {
    background: #1a202c !important;
    border: 1px solid #4a5568 !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}

/* Scroll styling for sidebar */
.sidebar::-webkit-scrollbar {
    width: 6px !important;
}

.sidebar::-webkit-scrollbar-track {
    background: #1a202c !important;
}

.sidebar::-webkit-scrollbar-thumb {
    background: #4a5568 !important;
    border-radius: 3px !important;
}

.sidebar::-webkit-scrollbar-thumb:hover {
    background: #667eea !important;
}

/* Animation keyframes */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes glow {
    0%, 100% {
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    50% {
        box-shadow: 0 4px 25px rgba(102, 126, 234, 0.5);
    }
}

@keyframes slideIn {
    from {
        transform: translateX(-100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.conversation-item {
/* Essential Streamlit overrides only - detailed styles loaded from external CSS files */
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
        st.markdown(
            f'<div style="text-align: center; color: #a0aec0; margin-bottom: 1rem; font-size: 0.9rem;">'
            f'📝 Current: <strong>{current_conversation["title"]}</strong> '
            f'({current_conversation["total_messages"]} messages)</div>',
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
    
    # Initialize session ID
    if "session_id" not in st.session_state:
        st.session_state.session_id = st.session_state.session_key
    
    # Load conversation history from database
    if "messages" not in st.session_state:
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
        except Exception as e:
            # Silent migration failure - don't disrupt user experience
            pass
        finally:
            st.session_state.migration_checked = True


# Initialize session state
initialize_session_state()

# Enhanced Chat History Sidebar
with st.sidebar:
    # Sidebar Header with gradient
    # Get conversation count for display
    try:
        conv_count = len(st.session_state.chat_service.get_recent_conversations(limit=100))
    except:
        conv_count = 0
    
    st.markdown(f"""
        <div class="sidebar-header" style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                animation: rotate 20s linear infinite;
            "></div>
            
            <h2 style="
                color: white;
                margin: 0;
                font-size: 1.3rem;
                font-weight: 600;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                position: relative;
                z-index: 1;
            ">💬 Chat History</h2>
            <p style="
                color: rgba(255,255,255,0.9);
                margin: 0.5rem 0 0 0;
                font-size: 0.9rem;
                position: relative;
                z-index: 1;
            ">
                {conv_count} conversation{'s' if conv_count != 1 else ''} • Always saved
            </p>
        </div>
        
        <style>
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # Enhanced New Chat button
    new_chat_clicked = st.button(
        "✨ Start New Chat", 
        use_container_width=True,
        help="Begin a fresh conversation"
    )
    
    if new_chat_clicked:
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
        except Exception as e:
            st.error(f"Error starting new chat: {str(e)}")
    
    # Elegant divider
    st.markdown("""
        <div style="
            height: 2px;
            background: linear-gradient(90deg, transparent, #4a5568, transparent);
            margin: 1.5rem 0;
        "></div>
    """, unsafe_allow_html=True)
    
    # Recent Conversations Section
    try:
        recent_conversations = st.session_state.chat_service.get_recent_conversations(limit=8)
        
        if recent_conversations:
            st.markdown("""
                <div style="
                    color: #e2e8f0;
                    font-size: 1.1rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                ">
                    📚 Recent Conversations
                    <span style="
                        background: rgba(102, 126, 234, 0.2);
                        color: #667eea;
                        padding: 0.2rem 0.5rem;
                        border-radius: 10px;
                        font-size: 0.8rem;
                        font-weight: 500;
                    ">{}</span>
                </div>
            """.format(len(recent_conversations)), unsafe_allow_html=True)
            
            for i, conv in enumerate(recent_conversations):
                # Format conversation data
                display_title = conv['title']
                if len(display_title) > 28:
                    display_title = display_title[:25] + "..."
                
                created_date = conv['created_at'][:10]
                message_count = conv['total_messages']
                is_current = conv['session_id'] == st.session_state.session_id
                
                # Time ago calculation
                try:
                    from datetime import datetime
                    created_dt = datetime.fromisoformat(conv['created_at'])
                    now = datetime.now()
                    diff = now - created_dt
                    
                    if diff.days > 0:
                        time_ago = f"{diff.days}d ago"
                    elif diff.seconds > 3600:
                        time_ago = f"{diff.seconds//3600}h ago"
                    elif diff.seconds > 60:
                        time_ago = f"{diff.seconds//60}m ago"
                    else:
                        time_ago = "Just now"
                except:
                    time_ago = created_date
                
                # Create conversation card
                if is_current:
                    # Current conversation - special styling
                    st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            border: 2px solid #667eea;
                            border-radius: 12px;
                            padding: 1rem;
                            margin: 0.5rem 0;
                            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                            position: relative;
                            overflow: hidden;
                        ">
                            <div style="
                                position: absolute;
                                top: 0.5rem;
                                right: 0.5rem;
                                background: rgba(255,255,255,0.9);
                                color: #667eea;
                                padding: 0.2rem 0.5rem;
                                border-radius: 8px;
                                font-size: 0.7rem;
                                font-weight: 600;
                            ">ACTIVE</div>
                            
                            <div style="
                                color: white;
                                font-weight: 600;
                                font-size: 1rem;
                                margin-bottom: 0.5rem;
                                text-shadow: 0 1px 2px rgba(0,0,0,0.2);
                            ">� {display_title}</div>
                            
                            <div style="
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                color: rgba(255,255,255,0.9);
                                font-size: 0.8rem;
                            ">
                                <span>📅 {time_ago}</span>
                                <span style="
                                    background: rgba(255,255,255,0.2);
                                    padding: 0.2rem 0.5rem;
                                    border-radius: 8px;
                                    font-weight: 500;
                                ">💬 {message_count}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    # Non-current conversations - clickable cards
                    conversation_key = f"conv_card_{conv['id']}"
                    
                    # Create clickable button that looks like a card
                    if st.button(
                        f"💬 {display_title}",
                        key=conversation_key,
                        use_container_width=True,
                        help=f"Switch to '{conv['title']}' ({message_count} messages)"
                    ):
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
                            
                            st.success(f"📂 Loaded: {conv['title']}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error loading conversation: {str(e)}")
                    
                    # Add metadata below button
                    st.markdown(f"""
                        <div style="
                            color: #a0aec0;
                            font-size: 0.75rem;
                            margin: -0.5rem 0 0.5rem 0;
                            display: flex;
                            justify-content: space-between;
                            padding: 0 0.5rem;
                        ">
                            <span>📅 {time_ago}</span>
                            <span style="
                                background: rgba(102, 126, 234, 0.2);
                                color: #667eea;
                                padding: 0.1rem 0.4rem;
                                border-radius: 6px;
                                font-weight: 500;
                            ">💬 {message_count}</span>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            # No conversations found
            st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
                    border: 2px dashed #4a5568;
                    border-radius: 12px;
                    padding: 2rem 1rem;
                    text-align: center;
                    color: #a0aec0;
                    margin: 1rem 0;
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">💭</div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">No conversations yet</div>
                    <div style="font-size: 0.9rem; opacity: 0.8;">Start chatting to see your history here!</div>
                </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error loading chat history: {str(e)}")
    
    # Enhanced Database Statistics
    st.markdown("""
        <div style="
            height: 2px;
            background: linear-gradient(90deg, transparent, #4a5568, transparent);
            margin: 1.5rem 0;
        "></div>
    """, unsafe_allow_html=True)
    
    with st.expander("📊 Database Analytics", expanded=False):
        try:
            stats = st.session_state.chat_service.get_service_stats()
            db_stats = stats['database_stats']
            
            # Create metrics with custom styling
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "💬 Conversations", 
                    db_stats['conversations'],
                    help="Total number of chat conversations"
                )
                
            with col2:
                st.metric(
                    "💭 Messages", 
                    db_stats['messages'],
                    help="Total messages exchanged"
                )
            
            # Database size with custom display
            db_size_kb = db_stats['db_size_bytes'] / 1024
            if db_size_kb < 1024:
                size_display = f"{db_size_kb:.1f} KB"
            else:
                size_display = f"{db_size_kb/1024:.1f} MB"
            
            st.metric(
                "� Storage Used", 
                size_display,
                help="Database file size on disk"
            )
            
            # Service status indicator
            status = stats['service_status']
            status_color = "#48bb78" if status == "healthy" else "#f56565"
            
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
                    border: 1px solid {status_color};
                    border-radius: 8px;
                    padding: 0.75rem;
                    margin-top: 1rem;
                    text-align: center;
                ">
                    <span style="color: {status_color}; font-weight: 600;">
                        {'🟢' if status == 'healthy' else '🔴'} Service Status: {status.title()}
                    </span>
                </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")
    
    # Quick Actions (optional)
    st.markdown("""
        <div style="
            margin-top: 1rem;
            padding: 1rem;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 10px;
            border: 1px solid rgba(102, 126, 234, 0.2);
        ">
            <div style="
                color: #667eea;
                font-size: 0.9rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
                text-align: center;
            ">💡 Quick Tip</div>
            <div style="
                color: #a0aec0;
                font-size: 0.8rem;
                text-align: center;
                line-height: 1.4;
            ">
                Click any conversation to switch between your chats. Your progress is automatically saved!
            </div>
        </div>
    """, unsafe_allow_html=True)

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
                
            except Exception as e:
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

        response_index += 1  # Increment for next AI response

# Input form
st.markdown('<div class="input-container">', unsafe_allow_html=True)
with st.form(key="chat_form", clear_on_submit=True):
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
    """Enhanced AI response with better error handling"""
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

            # Check for error indicators in response
            error_indicators = [
                "http error",
                "request timed out",
                "an unexpected error occurred",
                "error:",
                "failed to",
            ]
            if any(indicator in reply.lower() for indicator in error_indicators):
                return False, f"AI Error: {reply}"

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
    except requests.exceptions.RequestException as e:
        return False, f"🌐 Network error: {str(e)}"
    except Exception as e:
        return False, f"❌ Unexpected error: {str(e)}"


# Handle message sending with enhanced features
if submitted and user_input:
    # Validate input
    is_valid, result = validate_input(user_input)

    if not is_valid:
        st.error(result)
    elif user_input != st.session_state.last_input:
        # Mark conversation as started
        if not st.session_state.conversation_started:
            st.session_state.conversation_started = True
            st.success("🚀 Conversation started!")

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

                    # Success notification
                    st.success(f"✅ Message delivered successfully!")

                else:
                    st.error(ai_response)
                    # Don't add failed responses to conversation history
                    st.session_state.messages.pop()  # Remove user message from session state
                    st.session_state.message_count -= 1
                    
        except Exception as e:
            st.error(f"❌ Error saving message: {str(e)}")
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
