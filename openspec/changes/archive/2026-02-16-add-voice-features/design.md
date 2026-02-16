## Context

The Speak app currently uses a LangGraph workflow with parallel execution of `chat_node` (Claude conversation) and `correction_node` (grammar analysis). Both nodes execute independently and stream results via SSE. The frontend is React/TypeScript with a custom SSE hook and context-based state management.

Adding voice capabilities requires:

- Frontend: Speech-to-text input and audio playback
- Backend: Text-to-speech conversion integrated into the graph workflow
- Coordination: Audio must be generated after chat response completes

**Current Graph Structure**:

```
         ┌──▶ chat_node ──────────────▶ END
         │
dispatch ──┤
         │
         └──▶ correction_node ─────────▶ END
```

## Goals / Non-Goals

**Goals:**

- Enable voice input using browser-native speech recognition (zero cost, low latency)
- Generate spoken AI responses using OpenAI TTS API
- Maintain parallel execution of corrections while adding TTS in series after chat
- Keep text input/output as fallback for unsupported browsers
- Minimize latency and cost for TTS

**Non-Goals:**

- Streaming TTS (start playing while chat is generating) - adds significant complexity
- Voice activity detection or auto-stop recording
- Multiple voice options or playback controls (pause, replay, speed)
- Offline TTS fallback
- Switching to Whisper API for STT (Web Speech API is sufficient)

## Decisions

### 1. Speech-to-Text: Web Speech API (Frontend)

**Decision**: Use browser-native Web Speech API instead of external service (Whisper, Google Cloud STT).

**Rationale**:

- Zero cost and no API key management
- Low latency (local processing)
- Good enough accuracy for conversational English
- Better privacy (no data sent externally)
- Simple integration with existing React components

**Alternatives Considered**:

- **Whisper API**: Higher accuracy but adds cost ($0.006/min), latency, and complexity. Not needed for conversational practice.
- **Google Cloud STT**: More mechanical, requires API setup, costs money.

**Trade-off**: Safari has limited Web Speech API support. Mitigation: Keep text input as primary method, show error message for unsupported browsers.

### 2. Text-to-Speech: OpenAI TTS API (Backend)

**Decision**: Use OpenAI `tts-1` model with `nova` voice, `opus` format.

**Rationale**:

- **Model**: `tts-1` (low latency) over `tts-1-hd` - latency is higher priority than marginal quality improvement
- **Voice**: `nova` - friendly, natural female voice suitable for language learning
- **Format**: `opus` - small file size (~50% smaller than mp3), good quality, native browser support

**Alternatives Considered**:

- **Gemini 2.0 Flash**: Still experimental, not production-ready
- **ElevenLabs**: Too expensive (~$300/month for moderate usage)
- **Google Cloud TTS**: More mechanical sounding, less natural

**Cost**: $15 per 1M characters. For 10,000 conversations/month (avg 100 chars each) = ~$15/month.

### 3. Graph Architecture: TTS in Series After Chat

**Decision**: Add `tts_node` in series after `chat_node`, not in parallel.

**Rationale**:

- TTS needs the complete chat response text as input
- Cannot start until chat completes
- Corrections can still run in parallel (independent of TTS)

**New Graph Structure**:

```
         ┌──▶ correction_node ─────────▶ END
         │
dispatch ──┤
         │
         └──▶ chat_node ──▶ tts_node ──▶ END
```

**Implementation**: Modify graph edges in `backend/graph.py`:

```python
graph.add_edge("chat_node", "tts_node")
graph.add_edge("tts_node", END)
```

### 4. TTS Timing: Batch (Not Streaming)

**Decision**: Wait for chat response to complete, then convert entire response to speech.

**Rationale**:

- Simpler implementation (no chunking, no partial audio)
- OpenAI TTS API doesn't support true streaming (returns complete audio)
- User sees text immediately, audio follows shortly after
- Latency is acceptable for conversational responses (~1-2 seconds for typical response)

**Alternative Considered**:

- **Streaming TTS**: Would require chunking text, managing multiple audio segments, complex playback coordination. Not worth the complexity for marginal UX improvement.

### 5. Audio Playback: Web Audio API (Frontend)

**Decision**: Use `AudioContext.decodeAudioData()` to play Opus audio.

**Rationale**:

- Native Opus support in modern browsers
- Simple API, low latency
- No need for UI controls (auto-play after response)

**Alternatives Considered**:

- **HTML5 `<audio>` element**: Limited Opus support in Safari, unnecessary UI controls
- **MediaSource API**: Overly complex, requires container format (WebM/MP4), overkill for simple playback

**UX Decision**: No special audio UI. Users see text and hear audio simultaneously. No progress bars, pause buttons, or visual indicators needed.

### 6. SSE Event Schema

**Decision**: Add new `audio_chunk` event type to existing SSE stream.

**Format**:

```typescript
event: audio_chunk
data: {
  "audio": "base64_encoded_opus_data",
  "format": "opus"
}
```

**Rationale**:

- Consistent with existing SSE pattern (`chat_response`, `correction`, etc.)
- Frontend already has SSE infrastructure
- Base64 encoding works well with JSON/SSE (no binary handling needed)

## Risks / Trade-offs

### Risk: Web Speech API Browser Compatibility

- **Impact**: Safari users may not be able to use voice input
- **Mitigation**: Keep text input as primary method, show clear error message for unsupported browsers, detect support on mount

### Risk: OpenAI TTS API Latency

- **Impact**: 1-2 second delay between text appearing and audio playing
- **Mitigation**: Acceptable for conversational practice, text appears immediately so users aren't blocked

### Risk: OpenAI TTS API Cost

- **Impact**: Could become expensive at scale ($15 per 1M chars)
- **Mitigation**: Monitor usage, consider rate limiting or usage caps if needed, cost is reasonable for MVP

### Risk: Audio Playback Failures

- **Impact**: Audio decode errors or AudioContext issues could break playback
- **Mitigation**: Wrap in try-catch, log errors, don't block text display, graceful degradation

### Risk: LangGraph State Management

- **Impact**: Adding TTS node could affect thread persistence or checkpointing
- **Mitigation**: Test with existing MemorySaver, ensure audio data doesn't bloat state (store reference, not full audio)

## Migration Plan

**Deployment Steps**:

1. Add `OPENAI_API_KEY` to backend environment variables
2. Install `openai` Python package (`uv add openai`)
3. Deploy backend changes (graph + TTS node + SSE events)
4. Deploy frontend changes (speech recognition + audio playback)
5. Test end-to-end flow in production

**Rollback Strategy**:

- Backend: Remove TTS node, revert graph edges, remove SSE audio events
- Frontend: Remove microphone button, remove audio playback hook
- No data migration needed (pure feature addition)

**Backward Compatibility**:

- Old frontend clients ignore `audio_chunk` events (no breaking changes)
- Text input/output continues to work as before
- No API contract changes

## Open Questions

_None - all key decisions resolved during design phase._
