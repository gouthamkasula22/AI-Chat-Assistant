# AI Chat Assistant

A sophisticated web-based chat application powered by Google's Gemini AI, built with Streamlit and FastAPI.

## 🚀 Features

- **Real-time AI Chat**: Interactive conversations with Google Gemini AI
- **Session Persistence**: Conversations persist across browser refreshes
- **Response Time Tracking**: Monitor AI response times for each message
- **Professional UI**: Dark theme with clean, responsive design
- **Error Handling**: Comprehensive error handling and user-friendly messages
- **Security**: Input validation and API error management

## 🏗 Architecture

### Frontend (Streamlit)
- **File**: `main.py`
- **Purpose**: Web interface with chat functionality
- **Features**: Session management, response time display, conversation history

### Backend (FastAPI)  
- **File**: `app.py`
- **Purpose**: REST API server for chat endpoints
- **Endpoints**: `/chat` - Process chat requests and return AI responses

### Services Layer
- **LLM Proxy** (`services/llm_proxy.py`): Google Gemini API integration
- **Error Handler** (`utils/error_handler.py`): Centralized error handling

### Data Models
- **Chat Models** (`models/chat_models.py`): Pydantic models for API communication

### Configuration
- **Config** (`config/config.py`): Environment variable management

## 🛠 Installation

### Prerequisites
- Python 3.8+
- Google AI API Key (Gemini)

### Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd "LLM Chatbot"
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac  
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_google_ai_api_key_here
   ```
   
   **Getting your API Key:**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Sign in with your Google account
   - Create a new API key
   - Copy the key to your `.env` file

## 🚀 Running the Application

### Start Backend Server
```bash
# In terminal 1
uvicorn app:app --reload --port 8000
```

### Start Frontend Interface  
```bash
# In terminal 2
streamlit run main.py
```

### Access the Application
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage Guide

### Starting a Conversation
1. Open the application in your browser
2. Type your message in the input field
3. Press Enter or click Send
4. View the AI response with timing information

### Features in Action
- **Session Persistence**: Refresh the page - your conversation remains
- **Clear Chat**: Use the "Clear Chat" button to start fresh  
- **Response Times**: Each AI response shows processing time
- **Error Handling**: Network issues display user-friendly messages

### API Usage
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "history": [
            {"role": "user", "content": "Hello!"}
        ]
    }
)

result = response.json()
print(result["reply"])
```

## 🔧 Configuration

### Environment Variables
- `GEMINI_API_KEY`: Your Google AI API key (required)

### Customization Options
- **Theme**: Modify CSS in `main.py` for different styling
- **Model**: Change AI model in `services/llm_proxy.py`
- **Timeouts**: Adjust request timeouts in LLM proxy settings
- **History Limit**: Modify conversation history length (default: 10 messages)

## 🧪 Testing

### Run Unit Tests
```bash
python -m pytest tests/
```

### Manual Testing Checklist
- [ ] Start conversation with AI
- [ ] Refresh page - conversation persists  
- [ ] Clear chat functionality works
- [ ] Response times display correctly
- [ ] Error handling for network issues
- [ ] API endpoints respond correctly

### Performance Testing
```bash
# Test API response times
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"history":[{"role":"user","content":"Hello"}]}'
```

## 🔍 Troubleshooting

### Common Issues

**Frontend won't start**
- Check if port 8501 is available
- Verify virtual environment is activated
- Ensure all dependencies are installed

**Backend API errors**
- Verify `GEMINI_API_KEY` in `.env` file
- Check if port 8000 is available  
- Confirm Google AI API key is valid

**AI not responding**
- Verify internet connection
- Check API key permissions
- Review error logs in terminal

**Session not persisting**
- Check browser localStorage is enabled
- Verify file permissions for temp files
- Clear browser cache if needed

### Log Files
- Application logs appear in terminal output
- Session data stored in `temp_session_*.json` files
- API errors logged with full stack traces

### Performance Optimization
- **Memory**: Session files auto-cleanup after inactivity
- **Network**: Request timeouts prevent hanging connections
- **UI**: Optimized CSS for fast rendering

## 📁 Project Structure

```
LLM Chatbot/
├── app.py                      # FastAPI backend server
├── main.py                     # Streamlit frontend application  
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── .env                        # Environment variables (create this)
├── .pylintrc                   # Code quality configuration
│
├── config/
│   └── config.py              # Configuration management
│
├── controllers/
│   └── chat_controller.py     # Business logic layer
│
├── models/
│   └── chat_models.py         # API data models
│
├── services/
│   └── llm_proxy.py           # Google Gemini API integration
│
├── utils/
│   └── error_handler.py       # Error handling utilities
│
├── tests/
│   └── test_llm_proxy.py      # Unit tests
│
└── temp_session_*.json        # Session persistence files
```

## 🔐 Security

### API Key Protection
- Environment variables for sensitive data
- No hardcoded credentials in source code
- API key validation before requests

### Input Validation
- Message content filtering
- Request size limits
- SQL injection prevention through Pydantic models

### Error Handling
- Sanitized error messages to users
- Detailed logging for developers
- Graceful degradation on failures

## 📊 Monitoring & Logging

### Application Metrics
- Response time tracking per request
- Error rate monitoring
- Session persistence statistics

### Logging Levels
- `INFO`: Normal application flow
- `WARNING`: Potential issues
- `ERROR`: Error conditions with stack traces

### Health Checks
- Backend API health endpoint
- Frontend connectivity status
- Database/file system checks

## 🚀 Deployment

### Local Development
- Follow installation instructions above
- Use development servers (uvicorn/streamlit)

### Production Deployment
- Use production WSGI server (gunicorn)
- Configure reverse proxy (nginx)
- Set up SSL certificates
- Environment-specific configuration

### Docker Deployment (Optional)
```dockerfile
# Dockerfile example
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000 8501
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Quality Standards
- Pylint score > 8.0
- Unit test coverage > 80%
- Black code formatting
- Type hints for all functions

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google AI for Gemini API
- Streamlit for the amazing web framework
- FastAPI for the robust backend framework
- The open-source community for inspiration

---

**Built with ❤️ using Python, Streamlit, and FastAPI**
