## Context

Current system uses frontend Web Speech API for speech-to-text, which produces transcriptions without punctuation and has inconsistent accuracy across browsers. The application is an English practice chat tool where users need high-quality transcriptions with proper punctuation and capitalization.

The existing architecture uses LangGraph for conversation flow (guardrail → chat_tts/correction) with SSE streaming. We need to integrate backend STT without disrupting this architecture.

User feedback indicates that press-and-hold microphone interaction is tiring. Users prefer click-to-toggle mode (click once to start, click again to stop and submit).

## Goals / Non-Goals

**Goals:**
- Improve STT accuracy and add punctuation/capitalization support
- Provide immediate transcription feedback (< 500ms time-to-first-recognition)
- Maintain current LangGraph architecture unchanged
- Support all major browsers (Chrome, Firefox, Safari)
- Keep costs low (< $0.001 per 10-second conversation)
- Use click-to-toggle recording interaction for better UX

**Non-Goals:**
- Modifying LangGraph structure or adding STT as a graph node
- Storing audio files in checkpoints (only store text conversations)
- Supporting text input alongside voice (voice-only for now)
- Self-hosting Whisper model (use OpenAI API)
- Supporting recordings longer than 60 seconds (conversational use case)

## Decisions

### Decision 1: STT Processing at API Endpoint (Outside Graph)

**Choice:** Process STT at the `/chat` endpoint before Graph execution, not as a Graph node.

**Rationale:**
- STT is input format conversion (like JSON parsing), not business logic
- Avoids storing audio blobs in LangGraph checkpoints (waste of space)
- Enables immediate emission of transcription event before Graph starts
- Keeps Graph state clean (only text messages, no audio_input/transcription fields)

**Alternatives Considered:**
- **Add stt_node to Graph**: Rejected because:
  - Would store audio in every checkpoint
  - Can't emit transcription until Graph reaches that node
  - Complicates Graph state schema unnecessarily
  - Semantically unclear (mixing I/O conversion with business logic)

### Decision 2: OpenAI Whisper API Over Self-Hosted

**Choice:** Use OpenAI Whisper API for transcription.

**Rationale:**
- Native punctuation and capitalization support
- High accuracy across accents and speaking speeds
- Low cost ($0.006/min = $0.001 per 10-second message)
- No infrastructure overhead (API handles scaling)
- ~300ms latency acceptable for quality gain

**Alternatives Considered:**
- **Self-hosted Whisper**: Rejected due to infrastructure cost and maintenance complexity
- **Continue Web Speech API**: Rejected due to punctuation issues and inconsistent quality

### Decision 3: MediaRecorder API with Format Detection

**Choice:** Use browser MediaRecorder API with automatic format detection and fallback.

**Rationale:**
- Native browser support, no external libraries needed
- Opus codec provides excellent compression (16kbps = ~20KB per 10 seconds)
- Format detection handles browser differences transparently

**Browser Support:**
- Chrome/Firefox: `audio/webm;codecs=opus` (preferred, smallest size)
- Safari: `audio/mp4` (fallback)
- Edge cases: `audio/wav` (final fallback)

**Alternatives Considered:**
- **Fixed format requirement**: Rejected, would break Safari compatibility
- **Third-party recording library**: Unnecessary, MediaRecorder is well-supported

### Decision 4: Click-to-Toggle Recording Mode

**Choice:** Use toggle-based recording (click to start, click again to stop and submit).

**Rationale:**
- More comfortable for extended conversations
- Reduces hand fatigue from holding button
- Better accessibility (users can rest between speaking)
- Clearer visual feedback (recording state persists)

**Implementation:**
- Button shows "🎤 開始錄音" when idle
- Button shows "⏹️ 停止並送出" when recording
- Single `isRecording` state toggles behavior

**Alternatives Considered:**
- **Press-and-hold mode**: Rejected due to user fatigue concerns
- **Voice activation**: Rejected due to complexity and false triggers

### Decision 5: SSE Event Flow with Immediate Transcription

**Choice:** Emit `transcription` event immediately after Whisper returns, before Graph execution.

**Event Order:**
1. User clicks stop → audio uploads (~100ms)
2. Backend calls Whisper API (~300ms)
3. **Emit `transcription` event** (user sees result at ~400ms)
4. Backend creates Graph input with transcribed text
5. Graph executes normally (guardrail → chat/correction)

**Rationale:**
- Provides instant feedback while AI processes response
- Follows existing SSE pattern (add new event type, no breaking changes)
- User sees their transcribed text before AI reply starts

## Risks / Trade-offs

### Risk: Increased Latency (~350ms)
**Mitigation:**
- Upload optimized with Opus compression (~20KB for 10s)
- Whisper API typically responds in 200-400ms
- Trade-off acceptable: quality improvement outweighs delay
- User sees transcription immediately, perceives system as responsive

### Risk: OpenAI API Dependency
**Mitigation:**
- Implement error handling with user-friendly messages
- Consider rate limiting if cost becomes an issue
- Monitor API status and have fallback error flow
- Current cost estimates ($1 per 1000 conversations) are sustainable

### Risk: Browser Compatibility
**Mitigation:**
- Format detection with multiple fallbacks ensures broad support
- Test on Chrome, Firefox, Safari before release
- Clear error messages if MediaRecorder unavailable

### Risk: Audio File Size Limits
**Mitigation:**
- Recommend 30-60 second limit for conversational context
- FastAPI default 1MB limit is sufficient (covers ~5 minutes at 16kbps)
- Consider adding client-side duration limit with warning

### Risk: Network Failures During Upload
**Mitigation:**
- Show "🎤 轉錄中..." placeholder immediately
- Handle fetch errors with retry logic
- Display clear error message if upload fails
- User can retry recording

## Migration Plan

**Phase 1: Backend STT Integration (1-2 hours)**
1. Modify `/chat` endpoint signature to accept `UploadFile`
2. Add Whisper API call before Graph execution
3. Emit new `transcription` SSE event
4. Test with Postman/curl (upload sample audio files)

**Phase 2: Frontend Recording (2-3 hours)**
1. Create `useAudioRecorder` hook with toggle mode
2. Test recording functionality in isolation
3. Verify blob formats across browsers

**Phase 3: Integration (1-2 hours)**
1. Add `sendAudio()` method to `useSSE` hook
2. Update `MessageInput` component to use audio recording
3. Handle `transcription` events in SSE stream
4. End-to-end testing

**Phase 4: Cleanup (30 minutes)**
1. Remove unused `useSpeechRecognition` hook
2. Clean up imports and schemas
3. Update documentation

**Rollback Strategy:**
- Keep Web Speech API code in git history
- If issues arise, can revert frontend changes independently
- Backend changes are additive (Graph unchanged), safe to deploy

## Open Questions

None - design is complete and ready for implementation.
