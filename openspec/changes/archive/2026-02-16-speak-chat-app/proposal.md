## Why

English learners need an accessible way to practice conversational English with immediate, natural grammar feedback. Existing solutions like Speak are mobile-focused and expensive. A web-based application can provide similar value with lower barriers to entry, focusing on natural, everyday English practice rather than formal writing correction.

## What Changes

- **New web application** with React frontend and FastAPI backend
- **AI-powered conversation partner** using LangGraph + Anthropic Claude for natural dialogue
- **Real-time grammar corrections** displayed as expandable accordions under user messages
- **Practice summaries** with AI-generated learning tips based on accumulated corrections
- **Persistent conversations** using LangGraph thread-based state (survives page refresh)
- **Streaming architecture** using Server-Sent Events for parallel AI response and correction delivery
- **Text-only interface** (voice streaming planned for future phase)

## Capabilities

### New Capabilities

- `ai-chat-conversation`: Real-time conversational AI partner that maintains natural, encouraging dialogue with users to practice English
- `grammar-correction`: Message-level grammar analysis that identifies issues, provides corrected versions, and explains errors in a friendly way
- `practice-summary`: On-demand summary generation that lists all corrections and provides AI-generated tips for focused practice
- `conversation-persistence`: Thread-based conversation state management that preserves chat history across page refreshes and sessions

### Modified Capabilities

<!-- No existing capabilities are being modified - this is a new application -->

## Impact

**New Code**:

- `frontend/` - React application with SSE client, chat UI, accordion components, and state management
- `backend/` - FastAPI application with LangGraph workflow, Anthropic integration, and SSE endpoints

**Dependencies**:

- Backend: FastAPI, LangGraph, Anthropic SDK, checkpointer (MemorySaver initially, Redis/Postgres for production)
- Frontend: React, Vite, SSE client library

**APIs**:

- `POST /chat` - Streaming endpoint for AI conversation and grammar corrections
- `POST /summary` - Request/response endpoint for practice summary generation

**Infrastructure**:

- LangGraph thread persistence storage (in-memory for development, external store for production)
- Environment variables for Anthropic API keys

**Future Considerations**:

- Voice streaming node (third LangGraph node for TTS)
- Notion MCP integration for summary sync
