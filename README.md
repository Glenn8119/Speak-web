# Speak - AI-Powered English Practice Chat

<div align="center">

**Practice English conversation with real-time grammar feedback**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude-orange?style=for-the-badge)](https://anthropic.com/)

</div>

---

## ✨ Features

- **🤖 AI Conversation Partner** - Chat naturally with an encouraging AI that helps you practice everyday English
- **📝 Real-time Grammar Correction** - Get instant feedback on grammar errors as you chat
- **⚡ Parallel Processing** - Chat response and grammar analysis run simultaneously for faster feedback
- **💾 Conversation Persistence** - Your conversations are saved and restored across page refreshes
- **📊 Practice Summaries** - Get AI-generated tips and pattern analysis for your grammar journey
- **🎯 Focus on Spoken English** - Corrections focus on natural speech patterns, not formal writing

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** with [uv](https://github.com/astral-sh/uv) package manager
- **Node.js 18+** with [pnpm](https://pnpm.io/)
- **Anthropic API Key** from [Anthropic Console](https://console.anthropic.com/)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd speak-web
   ```

2. **Install all dependencies**

   ```bash
   make install
   ```

3. **Configure environment variables**

   ```bash
   # Copy the example env file
   cp backend/.env.example backend/.env

   # Add your Anthropic API key
   # Edit backend/.env and add your key:
   # ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

4. **Start the development servers**

   ```bash
   make dev
   ```

5. **Open the app**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## 📁 Project Structure

```
speak-web/
├── backend/                   # Python/FastAPI backend
│   ├── endpoints/            # API route handlers
│   │   ├── chat.py          # Chat, history, and summary endpoints
│   │   └── health.py        # Health check endpoint
│   ├── schemas/             # Pydantic models
│   ├── utils/               # Utility functions
│   ├── graph.py             # LangGraph workflow definition
│   ├── main.py              # FastAPI application entry
│   └── dependencies.py      # Dependency injection
│
├── frontend/                  # React/Vite frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── context/         # React Context (ChatContext)
│   │   ├── hooks/           # Custom hooks (useSSE)
│   │   ├── types/           # TypeScript interfaces
│   │   └── App.tsx          # Main application
│   └── ...
│
├── openspec/                  # Project specifications
├── Makefile                   # Development commands
└── README.md                  # This file
```

---

## 🔧 Development Commands

All commands are run from the project root using `make`:

```bash
# Start both frontend and backend
make dev

# Start only frontend (port 5173)
make dev-frontend

# Start only backend (port 8000)
make dev-backend

# Install all dependencies
make install

# Install frontend dependencies only
make install-frontend

# Install backend dependencies only
make install-backend
```

### Additional Commands

```bash
# Frontend-specific
cd frontend && pnpm lint          # Lint frontend code
cd frontend && pnpm build         # Production build

# Backend-specific
cd backend && uv run python test_graph.py    # Test LangGraph workflow
cd backend && uv run uvicorn main:app --reload  # Run backend manually
```

---

## 🌐 Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Optional (defaults shown)
# LOG_LEVEL=INFO
```

> ⚠️ **Never commit your API keys!** The `.env` file is already in `.gitignore`.

See `backend/.env.example` for a template.

---

## 📡 API Endpoints

| Method | Endpoint               | Description                                        |
| ------ | ---------------------- | -------------------------------------------------- |
| POST   | `/chat`                | Stream AI response and grammar corrections via SSE |
| GET    | `/history/{thread_id}` | Retrieve conversation history                      |
| POST   | `/summary`             | Generate practice summary with AI tips             |
| GET    | `/health`              | Health check endpoint                              |

### SSE Events (from `/chat`)

| Event           | Description                |
| --------------- | -------------------------- |
| `thread_id`     | New conversation thread ID |
| `chat_response` | AI conversation response   |
| `correction`    | Grammar correction data    |
| `error`         | Node failure information   |
| `complete`      | Stream completion status   |

For detailed API documentation, visit http://localhost:8000/docs when the backend is running.

---

## 🏗️ Architecture

### LangGraph Workflow

The backend uses LangGraph for AI orchestration with parallel execution:

```
START → dispatch → ┬→ chat_node ────→ END
                   └→ correction_node → END
```

- **dispatch_node**: Entry point that fans out to parallel nodes
- **chat_node**: Generates friendly conversational AI responses
- **correction_node**: Analyzes grammar and returns structured corrections

Both nodes execute in parallel, streaming results via SSE as they complete.

### State Persistence

Conversation state is managed by LangGraph's checkpointer:

- **Development**: `MemorySaver` (in-memory)
- **Production**: Redis or PostgreSQL (configurable)

### Frontend Architecture

- **State Management**: React Context with reducer pattern
- **SSE Handling**: Custom `useSSE` hook with automatic reconnection
- **Components**: Modular design with ChatContainer, MessageInput, CorrectionAccordion, etc.

---

## 🚀 Deployment

### Production Considerations

1. **Switch Checkpointer**: Replace `MemorySaver` with Redis or PostgreSQL for persistent state
2. **CORS Configuration**: Update allowed origins in `backend/main.py`
3. **Rate Limiting**: Consider implementing rate limiting for public deployment
4. **Environment**: Use proper secret management for API keys

### Docker Deployment

```bash
# Coming soon - Docker support is planned for future releases
```

### Cloud Deployment Options

- **Backend**: Any Python-compatible host (Railway, Render, AWS Lambda, etc.)
- **Frontend**: Static hosting (Vercel, Netlify, CloudFront + S3)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [LangGraph](https://langchain-ai.github.io/langgraph/) for the AI workflow engine
- [Anthropic Claude](https://anthropic.com/) for powering the AI interactions
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
- [Vite](https://vitejs.dev/) for lightning-fast frontend development
