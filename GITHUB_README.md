# 🤖 AI Chat Assistant

> A professional, full-stack AI chat application powered by Google Gemini API with session persistence, real-time response tracking, and production-ready architecture.

## ✨ Features

- 🤖 **Real-time AI Chat** - Interactive conversations with Google Gemini AI
- 💾 **Session Persistence** - Conversations survive browser refreshes  
- ⚡ **Response Time Tracking** - Monitor AI response times for each message
- 🎨 **Professional UI** - Dark theme with clean, responsive design
- 🛡️ **Security First** - Input validation and secure API key management
- 🚫 **Error Handling** - Comprehensive error handling for all scenarios
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile
- 🔄 **Clean Architecture** - Modular, maintainable code structure

## 🏗️ Architecture

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐    API Calls    ┌─────────────────┐
│   Streamlit     │ ────────────→   │    FastAPI      │ ────────────→   │  Google Gemini  │
│   Frontend      │                 │    Backend      │                 │      API        │
│   (main.py)     │ ←──────────────  │   (app.py)      │ ←──────────────  │                 │
└─────────────────┘                 └─────────────────┘                 └─────────────────┘
         │                                   │
         │                                   │
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│ Session Storage │                 │ LLM Proxy       │
│ (JSON Files)    │                 │ Service         │
└─────────────────┘                 └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google AI API Key ([Get it here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-chat-assistant.git
   cd ai-chat-assistant
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env and add your Google AI API key
   GEMINI_API_KEY=your_api_key_here
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   uvicorn app:app --reload --port 8000
   ```

2. **Start the frontend (in a new terminal)**
   ```bash
   streamlit run main.py
   ```

3. **Open your browser**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000/docs

## 💻 Usage

1. Open the chat interface in your browser
2. Type your message in the input field
3. Press Enter or click Send
4. View AI responses with timing information
5. Use "Clear Chat" to start a new conversation

Your conversations are automatically saved and will persist even if you refresh the browser!

## 📁 Project Structure

```
ai-chat-assistant/
├── 📄 main.py                    # Streamlit frontend application
├── 📄 app.py                     # FastAPI backend server
├── 📄 requirements.txt           # Python dependencies
├── 📄 README.md                  # Project documentation
├── 📄 .env.example              # Environment variables template
├── 📄 .gitignore                # Git ignore rules
├── 📄 .pylintrc                 # Code quality configuration
│
├── 📁 config/
│   └── 📄 config.py             # Configuration management
│
├── 📁 controllers/
│   └── 📄 chat_controller.py    # Business logic layer
│
├── 📁 models/
│   └── 📄 chat_models.py        # API data models
│
├── 📁 services/
│   └── 📄 llm_proxy.py          # Google Gemini API integration
│
├── 📁 utils/
│   └── 📄 error_handler.py      # Error handling utilities
│
├── 📁 tests/
│   └── 📄 test_llm_proxy.py     # Unit tests
│
├── 📁 docs/
│   └── 📄 TESTING.md            # Testing procedures guide
│
└── 📁 Requirements/
    └── 📄 Project Requirements.md
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

For comprehensive testing procedures, see [docs/TESTING.md](docs/TESTING.md).

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google AI API key for Gemini | ✅ Yes |

### Customization Options

- **UI Theme**: Modify CSS in `main.py`
- **AI Model**: Change model in `services/llm_proxy.py` 
- **Session Duration**: Adjust session file cleanup
- **Response Limits**: Modify message history length

## 🛡️ Security Features

- 🔐 **API Key Protection** - Environment variables only, no hardcoded secrets
- 🛡️ **Input Validation** - Comprehensive sanitization and length limits
- 🔒 **Error Sanitization** - User-friendly messages, no sensitive data exposure  
- ⏱️ **Timeout Protection** - Prevents hanging connections
- 🚫 **XSS Prevention** - Input filtering and output sanitization

## 📊 Quality Metrics

- **Code Quality**: 9.36/10 Pylint score ✅
- **Security Scan**: Clean Bandit security scan ✅
- **Dependencies**: No known vulnerabilities ✅
- **Documentation**: Comprehensive guides ✅
- **Test Coverage**: High coverage of critical paths ✅

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google AI](https://ai.google.dev/) for the Gemini API
- [Streamlit](https://streamlit.io/) for the amazing web framework  
- [FastAPI](https://fastapi.tiangolo.com/) for the robust backend framework
- The open-source community for inspiration and tools

---

<div align="center">

**Built with ❤️ using Python, Streamlit, and FastAPI**

[⭐ Star this repo](https://github.com/yourusername/ai-chat-assistant) | [🐛 Report Bug](https://github.com/yourusername/ai-chat-assistant/issues) | [✨ Request Feature](https://github.com/yourusername/ai-chat-assistant/issues)

</div>
