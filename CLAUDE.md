# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Speak is an English practice chat application with AI-powered conversation and grammar correction. Users chat with an AI conversation partner who provides friendly responses while a parallel system analyzes grammar errors in their messages.

## Commands

```bash
# Development
make dev              # Start both frontend (5173) and backend (8000)
make dev-frontend     # Start frontend only
make dev-backend      # Start backend only

# Dependencies
make install          # Install all dependencies
make install-frontend # pnpm install in frontend/
make install-backend  # uv sync in backend/

# Frontend
cd frontend && pnpm lint    # Lint frontend code
cd frontend && pnpm build   # Build frontend

# Backend
cd backend && uv run python test_graph.py  # Run graph workflow test
cd backend && uv run uvicorn main:app --reload  # Run backend manually
```

## Architecture

### Backend (Python/FastAPI)

**LangGraph Workflow** ([backend/graph.py](backend/graph.py)):
- `dispatch_node` → fans out to parallel execution
- `chat_node` → generates conversational AI response using Claude
- `correction_node` → analyzes grammar and returns structured corrections
- Both nodes execute in parallel via LangGraph, streaming results independently

**API Endpoints** ([backend/endpoints/chat.py](backend/endpoints/chat.py)):
- `POST /chat` - SSE streaming endpoint for chat + corrections
- `POST /summary` - Generate conversation summary
- `GET /history/{thread_id}` - Retrieve conversation history
- `GET /health` - Health check

**SSE Events**: `thread_id`, `chat_response`, `correction`, `error`, `complete`

Thread persistence uses LangGraph checkpointing (MemorySaver in dev).

### Frontend (React/TypeScript)

**State Management**: React Context in [ChatContext.tsx](frontend/src/context/ChatContext.tsx) with reducer pattern

**SSE Hook**: [useSSE.ts](frontend/src/hooks/useSSE.ts) handles Server-Sent Events connection, parsing, and automatic reconnection with exponential backoff

**Data Flow**:
1. User sends message → `useSSE.sendMessage()`
2. POST to `/chat` with SSE streaming
3. Parse SSE events → update ChatContext state
4. Components re-render with new messages/corrections

## Environment

Backend requires `ANTHROPIC_API_KEY` in `backend/.env` (see `.env.example`)
