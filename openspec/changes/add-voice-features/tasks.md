## 1. Backend Setup

- [ ] 1.1 Add `openai` package to backend dependencies (uv add openai)
- [ ] 1.2 Add `OPENAI_API_KEY` to backend/.env.example
- [ ] 1.3 Update backend/.env with actual OpenAI API key

## 2. Backend TTS Node Implementation

- [ ] 2.1 Create TTS node function in backend/graph.py
- [ ] 2.2 Implement OpenAI TTS API call (model: tts-1, voice: nova, format: opus)
- [ ] 2.3 Add base64 encoding for audio data
- [ ] 2.4 Add error handling for TTS API failures (log error, continue without audio)
- [ ] 2.5 Add error handling for empty/null chat responses (skip TTS)
- [ ] 2.6 Ensure TTS node does NOT add audio bytes to graph state (avoid bloating checkpoints)

## 3. Backend Graph Modification

- [ ] 3.1 Modify graph edges to add tts_node in series after chat_node
- [ ] 3.2 Update graph structure: dispatch → chat_node → tts_node → END
- [ ] 3.3 Keep correction_node in parallel (dispatch → correction_node → END)
- [ ] 3.4 Test graph execution order with LangGraph checkpointing

## 4. Backend SSE Streaming

- [ ] 4.1 Add 'audio_chunk' SSE event type to backend/endpoints/chat.py
- [ ] 4.2 Stream audio_chunk event with base64 audio and format 'opus' after TTS completes
- [ ] 4.3 Ensure audio_chunk events are sent per message (not shared across thread)
- [ ] 4.4 Test SSE streaming with multiple messages in same thread

## 5. Frontend Speech Recognition Hook

- [ ] 5.1 Create frontend/src/hooks/useSpeechRecognition.ts
- [ ] 5.2 Initialize SpeechRecognition with language 'en-US', continuous: false, interimResults: true
- [ ] 5.3 Implement start/stop recording functions
- [ ] 5.4 Handle interim results (update input field in real-time)
- [ ] 5.5 Handle final results (update input field, stop recording, auto-submit)
- [ ] 5.6 Add error handling for recognition errors (network, no-speech, aborted)
- [ ] 5.7 Add browser support detection (disable mic button if unsupported)
- [ ] 5.8 Add timeout handling (stop recording if no speech detected)

## 6. Frontend Audio Playback Hook

- [ ] 6.1 Create frontend/src/hooks/useAudioPlayback.ts
- [ ] 6.2 Initialize AudioContext on mount
- [ ] 6.3 Implement base64 → ArrayBuffer → AudioBuffer decoding
- [ ] 6.4 Implement audio playback using AudioContext.createBufferSource()
- [ ] 6.5 Add error handling for audio decode failures (log error, don't block text)
- [ ] 6.6 Handle AudioContext suspended state (resume on user interaction)
- [ ] 6.7 Implement auto-play after text display completes

## 7. Frontend SSE Integration

- [ ] 7.1 Update frontend/src/hooks/useSSE.ts to handle 'audio_chunk' events
- [ ] 7.2 Parse audio_chunk event data (extract base64 audio and format)
- [ ] 7.3 Integrate with useAudioPlayback hook to play audio
- [ ] 7.4 Ensure audio playback doesn't block text display

## 8. Frontend UI Updates

- [ ] 8.1 Add microphone button to frontend/src/components/ChatInput.tsx
- [ ] 8.2 Show recording state UI (visual indicator when recording)
- [ ] 8.3 Display error message if Web Speech API not supported
- [ ] 8.4 Ensure text input remains functional alongside voice input
- [ ] 8.5 Handle switching between voice and text input (clear interim transcript)
- [ ] 8.6 Add empty transcript handling (don't send message if transcript is empty)

## 9. Testing

- [ ] 9.1 Test TTS node generates valid Opus audio
- [ ] 9.2 Test SSE streams audio_chunk events correctly
- [ ] 9.3 Test graph executes in correct order (dispatch → chat → tts → END, correction in parallel)
- [ ] 9.4 Test error handling when OpenAI TTS API fails
- [ ] 9.5 Test microphone captures speech correctly
- [ ] 9.6 Test transcript displays in real-time (interim results)
- [ ] 9.7 Test audio plays after chat response appears
- [ ] 9.8 Test graceful degradation when Web Speech API not supported
- [ ] 9.9 Test no UI blocking during audio playback
- [ ] 9.10 Test end-to-end: speak → transcribe → chat → TTS → playback
- [ ] 9.11 Test corrections still work in parallel with TTS
- [ ] 9.12 Test thread persistence works with new TTS node
- [ ] 9.13 Test multiple messages in same thread (each gets own audio)

## 10. Documentation

- [ ] 10.1 Update README.md with voice feature description
- [ ] 10.2 Update backend/.env.example with OPENAI_API_KEY
- [ ] 10.3 Add browser compatibility notes to documentation
- [ ] 10.4 Document SSE event schema for audio_chunk
