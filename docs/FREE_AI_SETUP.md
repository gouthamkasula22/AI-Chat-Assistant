# Free AI Models Setup Guide

This guide helps you set up free AI models for the Advanced AI Features.

## 🆓 Available Free AI Models

### 1. Google Gemini Pro (Recommended)
- **Cost**: Completely FREE
- **Limits**: 15 requests/minute, 1500 requests/day
- **Quality**: Excellent for conversations
- **Setup**: 
  1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
  2. Click "Create API Key"
  3. Copy the key to your `.env` file as `GEMINI_API_KEY=your_key_here`

### 2. Hugging Face Models (Fallback Options)
- **Cost**: Completely FREE
- **Models Available**:
  - Microsoft DialoGPT Large
  - Facebook BlenderBot 400M
  - Microsoft DialoGPT Medium
- **Limits**: 
  - Without API token: 100 requests/hour
  - With API token: 1000 requests/hour
- **Setup**:
  1. Go to [Hugging Face](https://huggingface.co/settings/tokens)
  2. Create a "Read" token (optional but recommended)
  3. Add to `.env` file as `HUGGINGFACE_API_TOKEN=your_token_here`

## 🔧 Quick Setup

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Get Gemini API Key** (Primary model):
   - Visit: https://makersuite.google.com/app/apikey
   - Click "Create API Key"
   - Copy to `.env` file

3. **Optional: Get Hugging Face Token** (Better rate limits):
   - Visit: https://huggingface.co/settings/tokens
   - Create new token with "Read" permissions
   - Copy to `.env` file

4. **Test the setup**:
   - Run the app: `streamlit run main.py`
   - Go to sidebar → "🤖 AI Configuration"
   - Click "🧪 Test AI Models"

## 🎭 Conversation Styles Available

1. **Friendly Assistant** - Warm and encouraging
2. **Professional Assistant** - Formal and precise
3. **Creative Assistant** - Imaginative and innovative
4. **Analytical Assistant** - Logical and data-driven
5. **Casual Assistant** - Relaxed and informal
6. **Helpful Assistant** - Solution-focused (default)

## 🔄 How Model Fallback Works

1. **Primary**: Gemini Pro (if API key configured)
2. **Fallback 1**: DialoGPT Large (Hugging Face)
3. **Fallback 2**: BlenderBot 400M (Hugging Face)
4. **Fallback 3**: DialoGPT Medium (Hugging Face)
5. **Final Fallback**: Original backend API

## 📊 Rate Limits & Usage

- **Gemini**: 1500 free requests per day
- **Hugging Face**: 100-1000 requests per hour (depending on token)
- **No charges ever** - all models use free tiers only

## 🚀 Getting Started

1. **Minimum setup**: Just run the app! Hugging Face models work without any API keys
2. **Recommended setup**: Add Gemini API key for best quality
3. **Optimal setup**: Add both Gemini and Hugging Face tokens

The system automatically handles failures and switches between models seamlessly!
