# GEMINI.md

This file provides guidance to GEMINI when working with code in this repository.

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

- `guardrail_node` → entry point that classifies user intent (conversation vs task request)
- `chat_and_tts_node` (chat_tts) → generates AI response using Claude + converts to speech via OpenAI TTS
- `correction_node` → analyzes grammar and returns structured corrections
- `tts_node` → standalone TTS for guardrail rejection messages
- Flow: START → guardrail → [pass: chat_tts + correction in parallel] or [reject: tts only]

**API Endpoints** ([backend/endpoints/chat.py](backend/endpoints/chat.py)):

- `POST /chat` - SSE streaming endpoint for voice input → transcription → chat + corrections
  - Accepts multipart/form-data with audio file and optional thread_id
  - Uses OpenAI Whisper API for speech-to-text transcription
  - Returns AI response with TTS audio (OpenAI TTS API)
- `POST /summary` - Generate conversation summary with AI tips and IELTS vocabulary suggestions
  - Uses FAISS vector index with AWS Bedrock embeddings for RAG-based vocabulary recommendations
  - Runs tips generation and IELTS RAG pipeline in parallel
- `GET /history/{thread_id}` - Retrieve conversation history
- `GET /health` - Health check

**SSE Events**: `transcription`, `thread_id`, `chat_response`, `correction`, `audio_chunk`, `error`, `complete`

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
5. Guardrail checks message intent (conversation vs task request)
6. LangGraph routes based on guardrail result:
   - Pass: chat_tts + correction execute in parallel
   - Reject: tts generates audio for rejection message
7. TTS converts AI response to speech → emits `audio_chunk` event
8. Parse SSE events → update ChatContext state
9. Components re-render with transcription, AI response, corrections, and play audio

## Environment

Backend requires API keys in `backend/.env` (see `.env.example`):

**Required:**

- `ANTHROPIC_API_KEY`: For Claude AI chat, corrections, and guardrail classification
- `OPENAI_API_KEY`: For Whisper API (speech-to-text) and TTS API (text-to-speech)

**Optional (for IELTS RAG feature):**

- `AWS_ACCESS_KEY_ID`: For AWS Bedrock Embeddings
- `AWS_SECRET_ACCESS_KEY`: For AWS Bedrock Embeddings
- `AWS_REGION`: AWS region (e.g., us-east-1)

**IELTS RAG Feature**: The `/summary` endpoint includes AI-generated vocabulary suggestions using a FAISS vector index with AWS Bedrock embeddings. If AWS credentials are not configured, this feature gracefully degrades (returns empty suggestions).
