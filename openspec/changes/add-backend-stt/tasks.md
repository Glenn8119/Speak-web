## 1. Backend Environment Setup

- [ ] 1.1 Add `OPENAI_API_KEY` to `backend/.env`
- [ ] 1.2 Add `openai` package to backend dependencies (if not already present)
- [ ] 1.3 Verify OpenAI API key is valid by testing Whisper API access

## 2. Backend Endpoint Modification

- [ ] 2.1 Modify `/chat` endpoint signature in `backend/endpoints/chat.py` to accept `UploadFile` for audio parameter
- [ ] 2.2 Change `thread_id` parameter to use `Form()` instead of request body
- [ ] 2.3 Add audio file reading logic (`audio_bytes = await audio.read()`)
- [ ] 2.4 Add OpenAI client initialization for Whisper API
- [ ] 2.5 Implement Whisper API transcription call with error handling
- [ ] 2.6 Modify `event_generator()` to emit `transcription` SSE event immediately after Whisper returns
- [ ] 2.7 Ensure transcription event is emitted before `thread_id` event
- [ ] 2.8 Update Graph input creation to use transcribed text as HumanMessage content
- [ ] 2.9 Add error event emission for Whisper API failures

## 3. Backend Testing

- [ ] 3.1 Test `/chat` endpoint with Postman/curl using sample audio file (WebM format)
- [ ] 3.2 Verify `transcription` SSE event is emitted correctly with JSON payload
- [ ] 3.3 Verify Graph executes normally with transcribed text
- [ ] 3.4 Test error handling when Whisper API fails
- [ ] 3.5 Test with different audio formats (WebM, MP4, WAV)

## 4. Frontend Audio Recorder Hook

- [ ] 4.1 Create `frontend/src/hooks/useAudioRecorder.ts` file
- [ ] 4.2 Implement `getSupportedMimeType()` function with format detection fallbacks
- [ ] 4.3 Implement `startRecording()` function with MediaRecorder initialization
- [ ] 4.4 Implement `stopRecording()` function that returns audio Blob
- [ ] 4.5 Add microphone permission error handling
- [ ] 4.6 Add state management for `isRecording`, `audioBlob`, and `error`
- [ ] 4.7 Ensure MediaRecorder stream cleanup on stop

## 5. Frontend SSE Hook Updates

- [ ] 5.1 Add `sendAudio(audioBlob: Blob)` method to `useSSE` hook
- [ ] 5.2 Implement `executeAudioRequest()` function to upload audio as FormData
- [ ] 5.3 Add placeholder user message with "🎤 轉錄中..." when audio upload starts
- [ ] 5.4 Add `onTranscription()` handler for new `transcription` SSE event
- [ ] 5.5 Implement message content update to replace placeholder with transcribed text
- [ ] 5.6 Update SSE event switch statement to handle `transcription` event type
- [ ] 5.7 Remove `Content-Type` header from fetch (let browser set multipart boundary)
- [ ] 5.8 Return `sendAudio` in hook's return object

## 6. Frontend Context Updates

- [ ] 6.1 Add `UPDATE_MESSAGE_CONTENT` action to ChatContext reducer
- [ ] 6.2 Implement reducer logic to update message content by message ID
- [ ] 6.3 Export `updateMessageContent` action creator from context

## 7. Frontend Message Input Component

- [ ] 7.1 Import `useAudioRecorder` hook in `MessageInput.tsx`
- [ ] 7.2 Replace `useSpeechRecognition` usage with `useAudioRecorder`
- [ ] 7.3 Get `sendAudio` method from SSE context
- [ ] 7.4 Implement `handleMicClick()` with toggle mode logic
- [ ] 7.5 Update button UI to show "🎤 開始錄音" when idle
- [ ] 7.6 Update button UI to show "⏹️ 停止並送出" when recording
- [ ] 7.7 Add visual recording indicator (e.g., red background or pulsing animation)
- [ ] 7.8 Display microphone permission errors to user

## 8. Frontend Testing

- [ ] 8.1 Test microphone permission request flow
- [ ] 8.2 Test recording start/stop toggle interaction
- [ ] 8.3 Verify audio blob is created correctly with appropriate format
- [ ] 8.4 Test audio upload to backend via FormData
- [ ] 8.5 Verify "🎤 轉錄中..." placeholder appears immediately
- [ ] 8.6 Verify transcribed text replaces placeholder after SSE event
- [ ] 8.7 Test full conversation flow: record → transcribe → AI response
- [ ] 8.8 Test on Chrome (WebM/Opus format)
- [ ] 8.9 Test on Firefox (WebM/Opus format)
- [ ] 8.10 Test on Safari (MP4 format fallback)

## 9. Integration Testing

- [ ] 9.1 Test complete end-to-end flow: record → upload → transcribe → guardrail → chat → correction
- [ ] 9.2 Verify punctuation and capitalization in transcribed text
- [ ] 9.3 Test with different speech lengths (5s, 10s, 30s)
- [ ] 9.4 Test with different accents and speaking speeds
- [ ] 9.5 Verify time-to-first-recognition < 500ms
- [ ] 9.6 Test error recovery: microphone permission denied
- [ ] 9.7 Test error recovery: network failure during upload
- [ ] 9.8 Test error recovery: Whisper API failure
- [ ] 9.9 Verify thread_id persistence across multiple recordings

## 10. Cleanup and Documentation

- [ ] 10.1 Delete `frontend/src/hooks/useSpeechRecognition.ts` (no longer needed)
- [ ] 10.2 Remove unused imports related to Web Speech API
- [ ] 10.3 Update `backend/schemas/chat.py` - remove or deprecate `ChatRequest` if no longer used
- [ ] 10.4 Add comments explaining audio format detection logic
- [ ] 10.5 Update CLAUDE.md if needed with new architecture notes
- [ ] 10.6 Verify CORS settings in `backend/main.py` allow multipart/form-data
