# Property Listing AI System - Iteration 1

Production-ready AI-powered system for automatically generating professional property listings.

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

## 📚 Documentation

Comprehensive documentation is available in the `documentation/` folder:
- **[PROJECT_DOCUMENTATION.md](documentation/PROJECT_DOCUMENTATION.md)** - Complete project documentation
- **[IMPLEMENTATION_STATUS.md](documentation/IMPLEMENTATION_STATUS.md)** - Implementation status
- **[TESTING_GUIDE.md](documentation/TESTING_GUIDE.md)** - Testing guide

## 🔐 Security

**IMPORTANT**: Never commit `.env` files to git. They contain sensitive API keys.
- Use `.env.example` as a template
- Add your actual keys to `.env` (which is gitignored)

## 🏗️ Project Structure

```
iteration1/
├── src/                    # Source code
│   ├── core/              # Core business logic (workflow, nodes, state)
│   ├── models/            # Data models
│   └── utils/             # Utility functions
├── tests/                 # Test files
├── documentation/         # All documentation
├── app.py                 # Gradio UI
├── main.py                # Main entry point
└── requirements.txt       # Dependencies
```

## ✨ Features

- ✅ 7-node LangGraph workflow
- ✅ Input/Output guardrails for safety
- ✅ Web search enrichment (Tavily)
- ✅ LLM content generation (OpenAI)
- ✅ 85% latency reduction through optimization
- ✅ Production-grade error handling
- ✅ User-friendly Gradio UI

## 📝 License

[Add your license here]

## 👥 Contributors

[Add contributors here]
