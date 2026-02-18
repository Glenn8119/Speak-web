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
- `POST /chat` - SSE streaming endpoint for voice input → transcription → chat + corrections
  - Accepts multipart/form-data with audio file and optional thread_id
  - Uses OpenAI Whisper API for speech-to-text transcription
- `POST /summary` - Generate conversation summary
- `GET /history/{thread_id}` - Retrieve conversation history
- `GET /health` - Health check

**SSE Events**: `transcription`, `thread_id`, `chat_response`, `correction`, `error`, `complete`

Thread persistence uses LangGraph checkpointing (MemorySaver in dev).

### Frontend (React/TypeScript)

**State Management**: React Context in [ChatContext.tsx](frontend/src/context/ChatContext.tsx) with reducer pattern

**Audio Recording**: [useAudioRecorder.ts](frontend/src/hooks/useAudioRecorder.ts) handles microphone recording with cross-browser format detection (WebM/Opus, MP4, WAV)

**SSE Hook**: [useSSE.ts](frontend/src/hooks/useSSE.ts) handles Server-Sent Events connection, parsing, and automatic reconnection with exponential backoff

**Data Flow**:
1. User records voice → `useAudioRecorder` captures audio blob
2. Upload audio → `useSSE.sendAudio()` sends multipart/form-data
3. Backend transcribes audio (Whisper API) → emits `transcription` event
4. User message updated with transcribed text
5. LangGraph processes message → chat + correction nodes execute in parallel
6. Parse SSE events → update ChatContext state
7. Components re-render with transcription, AI response, and corrections

## Environment

Backend requires both `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` in `backend/.env` (see `.env.example`)
- `ANTHROPIC_API_KEY`: For Claude AI chat and corrections
- `OPENAI_API_KEY`: For Whisper API speech-to-text transcription
