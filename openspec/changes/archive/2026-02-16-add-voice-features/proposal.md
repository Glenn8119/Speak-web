## Why

The current text-based chat interface limits the naturalness of English practice. Users must type messages and read responses, which doesn't simulate real conversation. Adding voice input and output enables a more authentic language learning experience where users can practice speaking and listening skills, making the app more effective for conversational English practice.

## What Changes

- Add browser-based speech-to-text input using Web Speech API
- Add text-to-speech output for AI responses using OpenAI TTS API
- Modify LangGraph workflow to add `tts_node` in series after `chat_node`
- Update SSE streaming to include audio chunk events
- Add microphone button and recording state UI to chat input
- Add audio playback capability using Web Audio API
- Add OpenAI API dependency and environment configuration

## Capabilities

### New Capabilities

- `voice-input`: Browser-based speech recognition that converts user speech to text for chat messages
- `voice-output`: Text-to-speech conversion of AI responses using OpenAI TTS, streamed as audio chunks

### Modified Capabilities

_None - this is a pure addition without modifying existing capability requirements_

## Impact

**Backend**:

- `backend/graph.py`: Add `tts_node` and modify graph edges (chat → tts → END)
- `backend/endpoints/chat.py`: Add `audio_chunk` SSE event type
- `backend/.env`: Add `OPENAI_API_KEY` environment variable
- Dependencies: Add `openai` Python package

**Frontend**:

- `frontend/src/hooks/`: New hooks for speech recognition and audio playback
- `frontend/src/hooks/useSSE.ts`: Handle new `audio_chunk` events
- `frontend/src/components/ChatInput.tsx`: Add microphone button and recording UI
- No new npm dependencies (using native Web APIs)

**External Services**:

- New dependency on OpenAI TTS API (cost: ~$15 per 1M characters)

**Browser Compatibility**:

- Web Speech API: Full support in Chrome/Firefox/Edge, limited in Safari
- Opus audio decode: Full support in all modern browsers
