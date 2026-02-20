## 1. Backend Environment Setup

- [x] 1.1 Add `OPENAI_API_KEY` to `backend/.env`
- [x] 1.2 Add `openai` package to backend dependencies (if not already present)
- [x] 1.3 Verify OpenAI API key is valid by testing Whisper API access

## 2. Backend Endpoint Modification

- [x] 2.1 Modify `/chat` endpoint signature in `backend/endpoints/chat.py` to accept `UploadFile` for audio parameter
- [x] 2.2 Change `thread_id` parameter to use `Form()` instead of request body
- [x] 2.3 Add audio file reading logic (`audio_bytes = await audio.read()`)
- [x] 2.4 Add OpenAI client initialization for Whisper API
- [x] 2.5 Implement Whisper API transcription call with error handling
- [x] 2.6 Modify `event_generator()` to emit `transcription` SSE event immediately after Whisper returns
- [x] 2.7 Ensure transcription event is emitted before `thread_id` event
- [x] 2.8 Update Graph input creation to use transcribed text as HumanMessage content
- [x] 2.9 Add error event emission for Whisper API failures

## 3. Backend Testing

- [x] 3.1 Test `/chat` endpoint with Postman/curl using sample audio file (WebM format)
- [x] 3.2 Verify `transcription` SSE event is emitted correctly with JSON payload
- [x] 3.3 Verify Graph executes normally with transcribed text
- [x] 3.4 Test error handling when Whisper API fails
- [x] 3.5 Test with different audio formats (WebM, MP4, WAV)

## 4. Frontend Audio Recorder Hook

- [x] 4.1 Create `frontend/src/hooks/useAudioRecorder.ts` file
- [x] 4.2 Implement `getSupportedMimeType()` function with format detection fallbacks
- [x] 4.3 Implement `startRecording()` function with MediaRecorder initialization
- [x] 4.4 Implement `stopRecording()` function that returns audio Blob
- [x] 4.5 Add microphone permission error handling
- [x] 4.6 Add state management for `isRecording`, `audioBlob`, and `error`
- [x] 4.7 Ensure MediaRecorder stream cleanup on stop

## 5. Frontend SSE Hook Updates

- [x] 5.1 Add `sendAudio(audioBlob: Blob)` method to `useSSE` hook
- [x] 5.2 Implement `executeAudioRequest()` function to upload audio as FormData
- [x] 5.3 Add placeholder user message with "🎤 Transcribing..." when audio upload starts
- [x] 5.4 Add `onTranscription()` handler for new `transcription` SSE event
- [x] 5.5 Implement message content update to replace placeholder with transcribed text
- [x] 5.6 Update SSE event switch statement to handle `transcription` event type
- [x] 5.7 Remove `Content-Type` header from fetch (let browser set multipart boundary)
- [x] 5.8 Return `sendAudio` in hook's return object

## 6. Frontend Context Updates

- [x] 6.1 Add `UPDATE_MESSAGE_CONTENT` action to ChatContext reducer
- [x] 6.2 Implement reducer logic to update message content by message ID
- [x] 6.3 Export `updateMessageContent` action creator from context

## 7. Frontend Message Input Component

- [x] 7.1 Import `useAudioRecorder` hook in `MessageInput.tsx`
- [x] 7.2 Replace `useSpeechRecognition` usage with `useAudioRecorder`
- [x] 7.3 Get `sendAudio` method from SSE context
- [x] 7.4 Implement `handleMicClick()` with toggle mode logic
- [x] 7.7 Add visual recording indicator (e.g., red background or pulsing animation)
- [x] 7.8 Display microphone permission errors to user

## 8. Frontend Testing

- [x] 8.1 Test microphone permission request flow
- [x] 8.2 Test recording start/stop toggle interaction
- [x] 8.3 Verify audio blob is created correctly with appropriate format
- [x] 8.4 Test audio upload to backend via FormData
- [x] 8.5 Verify "🎤 Transcribing..." placeholder appears immediately
- [x] 8.6 Verify transcribed text replaces placeholder after SSE event
- [x] 8.7 Test full conversation flow: record → transcribe → AI response

## 9. Integration Testing

- [x] 9.1 Test complete end-to-end flow: record → upload → transcribe → guardrail → chat → correction
- [x] 9.2 Verify punctuation and capitalization in transcribed text
- [x] 9.3 Test with different speech lengths (5s, 10s, 30s)
- [x] 9.4 Test with different accents and speaking speeds
- [x] 9.5 Verify time-to-first-recognition < 500ms
- [x] 9.6 Test error recovery: microphone permission denied
- [x] 9.7 Test error recovery: network failure during upload
- [x] 9.8 Test error recovery: Whisper API failure
- [x] 9.9 Verify thread_id persistence across multiple recordings

## 10. Cleanup and Documentation

- [x] 10.1 Delete `frontend/src/hooks/useSpeechRecognition.ts` (no longer needed)
- [x] 10.2 Remove unused imports related to Web Speech API
- [x] 10.3 Update `backend/schemas/chat.py` - remove or deprecate `ChatRequest` if no longer used
- [x] 10.4 Add comments explaining audio format detection logic
- [x] 10.5 Update CLAUDE.md if needed with new architecture notes
- [x] 10.6 Verify CORS settings in `backend/main.py` allow multipart/form-data
