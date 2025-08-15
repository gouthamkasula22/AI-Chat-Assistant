import streamlit as st
import requests

st.set_page_config(page_title="Gemini Chatbot", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
    .user-msg {background-color: #808080; border-radius: 10px; padding: 8px; margin-bottom: 5px;}
    .assistant-msg {background-color: #000000; border-radius: 10px; padding: 8px; margin-bottom: 5px;}
    .avatar {width: 32px; height: 32px; border-radius: 50%; display: inline-block; vertical-align: middle; margin-right: 8px;}
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("💡 How to use")
st.sidebar.info("Type your message below and get a response from Gemini!\n\nYour conversation is private.")

st.title("🤖 Gemini Chatbot")
st.caption("Powered by Google Gemini 2.0 Flash")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Gemini is thinking..."):
        response = requests.post(
            "http://localhost:8000/chat",
            json={"message": user_input}
        )
        reply = response.json().get("reply", "")
        st.session_state.messages.append({"role": "assistant", "content": reply})

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="user-msg"><img src="https://img.icons8.com/color/48/000000/user.png" class="avatar"/>**You:**<br>{msg["content"]}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="assistant-msg"><img src="https://img.icons8.com/color/48/000000/robot.png" class="avatar"/>**Gemini:**<br>{msg["content"]}</div>',
            unsafe_allow_html=True
        )