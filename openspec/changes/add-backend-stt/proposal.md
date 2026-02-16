## Why

Current frontend STT using Web Speech API produces transcriptions without punctuation and has medium accuracy. Users need better transcription quality with proper punctuation and capitalization for effective English practice conversations.

## What Changes

- Replace frontend Web Speech API with backend OpenAI Whisper API transcription
- Add frontend audio recording using MediaRecorder API with click-to-toggle interaction (click to start, click again to stop and submit)
- Modify `/chat` endpoint to accept audio file uploads via multipart/form-data
- Add new `transcription` SSE event to immediately return transcribed text before graph execution
- Update frontend SSE handling to process audio uploads and display transcription results

## Capabilities

### New Capabilities
- `backend-stt-transcription`: Backend speech-to-text capability using OpenAI Whisper API
- `frontend-audio-recording`: Frontend audio recording capability using MediaRecorder API with toggle-based interaction

### Modified Capabilities
- `chat-streaming`: Chat endpoint now accepts both text messages and audio files, emits new transcription event type

## Impact

**Backend**:
- `backend/endpoints/chat.py`: Endpoint signature change to accept audio upload, add Whisper API integration
- `backend/schemas/chat.py`: May remove or deprecate text-only ChatRequest schema
- Environment: Requires `OPENAI_API_KEY` configuration

**Frontend**:
- `frontend/src/hooks/useSSE.ts`: Add `sendAudio()` method and transcription event handler
- `frontend/src/hooks/useAudioRecorder.ts`: New hook for audio recording with toggle mode
- `frontend/src/components/MessageInput.tsx`: Update to use audio recording instead of Web Speech API
- `frontend/src/context/ChatContext.tsx`: Add message content update action for transcription display

**Cross-browser compatibility**: Need to handle different audio format support (WebM/Opus for Chrome/Firefox, MP4 for Safari)
