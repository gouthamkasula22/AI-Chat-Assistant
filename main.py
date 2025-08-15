import streamlit as st
import requests
import time
import uuid

st.set_page_config(
    page_title="AI Chat Assistant", 
    page_icon="💬", 
    layout="centered"
)

# Force session state to persist across refreshes
@st.cache_data(persist=True, show_spinner=False)
def get_persistent_session_id():
    """Generate a persistent session ID that survives browser refreshes"""
    return str(uuid.uuid4())

# Custom CSS for clean, professional look
st.markdown("""
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
    display: none;
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
</style>
""", unsafe_allow_html=True)

# Title and subtitle
st.markdown('<h1 class="main-title">💬 AI Chat Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Powered by Google Gemini AI</p>', unsafe_allow_html=True)

# Initialize persistent session state 
def initialize_session_state():
    """Initialize session state with persistent conversation data"""
    
    # Create a unique session key that persists across refreshes
    if "session_key" not in st.session_state:
        st.session_state.session_key = get_persistent_session_id()
    
    # Initialize conversation data with persistence
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_input" not in st.session_state:
        st.session_state.last_input = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = st.session_state.session_key
    if "message_count" not in st.session_state:
        st.session_state.message_count = 0
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False
    if "last_response_time" not in st.session_state:
        st.session_state.last_response_time = None
    if "total_response_time" not in st.session_state:
        st.session_state.total_response_time = 0
    if "response_times" not in st.session_state:
        st.session_state.response_times = []  # Track individual response times

# Initialize session state
initialize_session_state()

# Enhanced clear chat button and session info
col1, col2, col3 = st.columns([2, 1, 1])

# Remove the statistics box - we'll show response times with each message instead

# Force button visibility with additional CSS
st.markdown("""
<style>
[data-testid="stButton"] {
    visibility: visible !important;
    opacity: 1 !important;
}
[data-testid="stButton"] > button {
    visibility: visible !important;
    opacity: 1 !important;
    display: block !important;
}
</style>
""", unsafe_allow_html=True)

with col2:
    if st.session_state.messages:
        if st.button("📊 Stats", key="stats_btn", use_container_width=True):
            avg_response_time = st.session_state.total_response_time / max(1, len(st.session_state.response_times))
            st.info(f"""
            **Conversation Statistics:**
            - Total Messages: {st.session_state.message_count}
            - User Messages: {st.session_state.message_count // 2}
            - AI Responses: {len(st.session_state.response_times)}
            - Average Response Time: {avg_response_time:.1f}s
            - Session ID: {st.session_state.session_id[:12]}...
            """)

with col3:
    if st.session_state.messages:
        # Create a more visible clear button with debug info
        st.markdown(f"""
        <div style="background: #dc3545; color: white; padding: 0.5rem; 
                    border-radius: 5px; text-align: center; margin-bottom: 0.5rem;
                    font-size: 0.8rem;">
            Clear Chat Available ({len(st.session_state.messages)} messages)
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear Chat", key="clear_btn", use_container_width=True, help="Clear all messages"):
            # Clear all conversation data
            st.session_state.messages = []
            st.session_state.message_count = 0
            st.session_state.conversation_started = False
            st.session_state.last_response_time = None
            st.session_state.total_response_time = 0
            st.session_state.last_input = None
            st.session_state.response_times = []  # Clear response times too
            
            st.success("✅ Chat cleared! Starting fresh conversation.")
            time.sleep(0.5)  # Brief pause for user feedback
            st.rerun()

# Display chat messages with response times below each AI response
response_index = 0  # Track AI response index separately
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.markdown(f"""
        <div class="user-message">
            <strong>You:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        # AI response with response time below
        st.markdown(f"""
        <div class="assistant-message">
            <strong>AI Assistant:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
        
        # Show response time for this specific response if available
        if hasattr(st.session_state, 'response_times') and response_index < len(st.session_state.response_times):
            response_time = st.session_state.response_times[response_index]
            st.markdown(f"""
            <div style="text-align: right; margin: 0.5rem 15% 1rem 0;">
                <small style="color: #10b981; background: rgba(16, 185, 129, 0.1); 
                              padding: 0.3rem 0.8rem; border-radius: 10px; 
                              border: 1px solid rgba(16, 185, 129, 0.3);">
                    ⚡ Response time: {response_time:.1f}s
                </small>
            </div>
            """, unsafe_allow_html=True)
        
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
            label_visibility="collapsed"
        )
    with col2:
        submitted = st.form_submit_button("➤", help="Send message")

st.markdown("""
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
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

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
    harmful_patterns = ['<script', 'javascript:', 'onload=', 'onerror=']
    if any(pattern in text.lower() for pattern in harmful_patterns):
        return False, "Invalid characters detected."
    
    # Check for spam (repeated characters)
    if any(char * 10 in text for char in 'abcdefghijklmnopqrstuvwxyz'):
        return False, "Please avoid repeated characters."
    
    return True, text

def get_ai_response(messages, session_id):
    """Enhanced AI response with better error handling"""
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={
                "history": messages,
                "session_id": session_id
            },
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            reply = data.get("reply", "").strip()
            
            if not reply:
                return False, "Received empty response from AI."
            
            # Check for error indicators in response
            error_indicators = ["http error", "request timed out", "an unexpected error occurred", "error:", "failed to"]
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
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": result})
        st.session_state.last_input = user_input
        st.session_state.message_count += 1
        
        # Show typing indicator
        with st.spinner("🤖 AI is analyzing your message..."):
            start_time = time.time()
            
            # Get AI response
            success, ai_response = get_ai_response(
                st.session_state.messages, 
                st.session_state.session_id
            )
            
            elapsed = time.time() - start_time
            
            if success:
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                st.session_state.message_count += 1
                st.session_state.last_response_time = elapsed
                st.session_state.total_response_time += elapsed
                
                # Store individual response time
                st.session_state.response_times.append(elapsed)
                
                # Simple success notification without large response time box
                st.success(f"✅ Message delivered successfully!")
                
            else:
                st.error(ai_response)
                # Don't add failed responses to conversation history
                st.session_state.messages.pop()  # Remove user message if AI failed
                st.session_state.message_count -= 1
        
        st.rerun()

# Welcome message for empty chat with clean, simple design
if not st.session_state.messages:
    st.markdown("""
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
    """, unsafe_allow_html=True)
    
    # Simple session info display
    st.markdown(f"""
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
    """, unsafe_allow_html=True)