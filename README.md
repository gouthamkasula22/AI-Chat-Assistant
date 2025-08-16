# AI Chat Assistant

A personal project I built to experiment with multiple free AI models in one clean interface. Started simple and evolved into something pretty cool with chat history, multiple conversation styles, and a GitHub Copilot-inspired UI.

## What This Is

I wanted to build a chatbot that could switch between different AI models without paying for expensive APIs. After some research, I found several free options and decided to create a single interface to try them all out. The result is this web app that lets you chat with Google Gemini, Microsoft's DialoGPT, and Facebook's BlenderBot models.

## Why I Built This

- **Free AI models only** - No subscription fees or per-token charges
- **Compare different models** - See how each AI responds to the same prompt  
- **Clean, simple interface** - Inspired by GitHub Copilot's model selection
- **Persistent chat history** - Never lose your conversations
- **Different conversation styles** - From professional to creative

## Features That Actually Work

✅ **Multiple Free AI Models**
- Google Gemini Pro (15 requests/min free tier)
- Microsoft DialoGPT Large & Medium
- Facebook BlenderBot 400M

✅ **Smart Model Switching**
- Choose your AI model right in the input area
- Automatic fallback if one model fails
- No interruption to your conversation

✅ **Conversation Styles**
- Professional, Friendly, Creative, Analytical, Casual, Helpful
- Each style adjusts the AI's personality and response tone

✅ **Chat History That Persists**
- SQLite database stores all your conversations
- Browse previous chats in the sidebar
- Never lose an important conversation

✅ **Clean Interface**
- Dark theme that's easy on the eyes
- Inline model selection (no cluttered sidebars)

## Getting Started

### What You'll Need
- Python 3.8 or newer
- A free Google AI API key (takes 2 minutes to get)

### Setup (5 minutes max)

1. **Get the code**
   ```bash
   git clone https://github.com/gouthamkasula22/AI-Chat-Assistant.git
   cd "AI-Chat-Assistant"
   ```

2. **Install stuff**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get your free API key**
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Sign in and create a new API key
   - Copy it

4. **Create a .env file**
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

5. **Run it**
   ```bash
   streamlit run main.py
   ```

That's it! Open your browser to `http://localhost:8501` and start chatting.

## How to Use It

1. **Pick your AI model** from the dropdown (Gemini Pro, DialoGPT-L, BlenderBot, etc.)
2. **Choose a conversation style** (Professional, Creative, Friendly, etc.)
3. **Start typing** - that's literally it
4. **Switch models anytime** - your conversation continues seamlessly
5. **Check the sidebar** for your chat history

## The Models I'm Using

**Google Gemini Pro** - Google's latest model, pretty smart, 15 free requests per minute

**DialoGPT Large** - Microsoft's conversational AI, good for natural chat

**DialoGPT Medium** - Faster version of the above, still decent quality

**BlenderBot 400M** - Facebook's chatbot, interesting personality

All of these are completely free to use (with rate limits), which was my main requirement.

## What Makes This Different

Most AI chat apps lock you into one expensive model. I wanted to experiment with different approaches:

- **Strategy Pattern Architecture** - Easy to add new AI models
- **Automatic Fallback System** - If one model fails, try another
- **Rate Limit Handling** - Respects API limits gracefully  
- **Conversation Context** - Models remember what you talked about
- **Professional UI** - No flashy animations, just clean functionality

## Project Structure

```
├── main.py                 # Streamlit app (the main interface)
├── database/
│   └── db_manager.py      # SQLite database handling
├── services/
│   ├── chat_history_service.py    # Chat persistence logic
│   └── advanced_ai_service.py     # AI model coordination
├── models/
│   ├── ai_strategy.py            # Strategy pattern for AI models
│   ├── gemini_strategy.py        # Google Gemini integration
│   └── huggingface_strategy.py   # HuggingFace models (DialoGPT, BlenderBot)
└── docs/
    └── FREE_AI_SETUP.md          # Detailed setup guide
```

## If Something Breaks

**App won't start?**
- Make sure you're in the right directory
- Check that you installed requirements.txt
- Verify your Python version (3.8+)

**No AI responses?**
- Check your .env file has the API key
- Make sure you have internet connection
- Try switching to a different model

**Conversations not saving?**
- The app creates a SQLite database automatically
- Check file permissions in your directory

## Future Ideas

Things I might add if I have time:
- More free AI models (always looking for new ones)
- Export conversations to markdown
- Model performance comparison dashboard
- Custom conversation styles
- Maybe a mobile-friendly version

## Contributing

If you find this useful and want to improve it:
1. Fork it
2. Make your changes
3. Test that it still works
4. Send a pull request

I'm especially interested in:
- New free AI model integrations
- UI/UX improvements
- Performance optimizations
- Bug fixes

## Why Open Source

I learned a lot building this and figured others might find it useful. The code shows how to:
- Integrate multiple AI APIs
- Handle rate limits and fallbacks
- Build a clean Streamlit interface
- Implement the Strategy pattern in Python
- Create persistent chat storage

Feel free to use this as a starting point for your own AI projects.

---

**Built with Python, Streamlit, and a lot of coffee ☕**

*If you like this project, give it a star! It helps me know if this is worth maintaining.*
