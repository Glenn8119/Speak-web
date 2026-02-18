# Backend STT Transcription

## Purpose

This capability handles server-side speech-to-text transcription using OpenAI's Whisper API. The backend accepts audio file uploads, transcribes them using Whisper, and emits the transcribed text via SSE events before processing the message through the conversation graph.

## Requirements

### Requirement: Accept Audio File Upload

The backend `/chat` endpoint SHALL accept audio file uploads via multipart/form-data in addition to text messages.

#### Scenario: Receive audio file

- **WHEN** frontend sends POST request to `/chat` with `audio` field as UploadFile
- **THEN** the system reads the audio bytes and prepares for transcription

#### Scenario: Receive thread_id with audio

- **WHEN** frontend includes `thread_id` as Form parameter alongside audio
- **THEN** the system uses the provided thread_id for conversation continuity

#### Scenario: Generate new thread_id

- **WHEN** frontend does not provide thread_id with audio upload
- **THEN** the system generates a new UUID thread_id for the conversation

### Requirement: Whisper API Transcription

The backend SHALL use OpenAI Whisper API to transcribe audio files to text with punctuation and capitalization.

#### Scenario: Successful transcription

- **WHEN** backend receives valid audio file
- **THEN** the system calls OpenAI Whisper API with model "whisper-1", language "en", and receives transcribed text with punctuation

#### Scenario: Transcription with punctuation

- **WHEN** user says "yesterday I went to the store"
- **THEN** Whisper returns "Yesterday, I went to the store." with proper capitalization and punctuation

#### Scenario: Whisper API failure

- **WHEN** Whisper API returns an error or times out
- **THEN** the system logs the error and emits SSE error event with message "Speech recognition failed"

### Requirement: Immediate Transcription Event

The backend SHALL emit transcription result as SSE event immediately before Graph execution.

#### Scenario: Emit transcription event first

- **WHEN** Whisper API returns transcription successfully
- **THEN** the system emits `event: transcription` with the transcribed text before starting Graph execution

#### Scenario: Transcription event format

- **WHEN** emitting transcription event
- **THEN** the event data includes `{"text": "transcribed content", "timestamp": <unix_timestamp>}`

#### Scenario: Transcription before thread_id

- **WHEN** processing audio upload
- **THEN** the system emits transcription event, then thread_id event, then proceeds with Graph streaming

### Requirement: Graph Integration

The backend SHALL create Graph input using transcribed text as HumanMessage content.

#### Scenario: Create Graph input from transcription

- **WHEN** transcription completes successfully
- **THEN** the system creates `input_state` with `messages: [HumanMessage(content=transcribed_text)]`

#### Scenario: Graph executes normally

- **WHEN** Graph input is created from transcribed text
- **THEN** the Graph executes its normal flow (guardrail → chat_tts/correction) without modification

#### Scenario: No audio stored in checkpoint

- **WHEN** Graph saves checkpoint
- **THEN** the checkpoint only contains text messages, not the original audio blob

### Requirement: Multi-format Audio Support

The backend SHALL accept audio files in multiple formats to support different browsers.

#### Scenario: WebM/Opus format

- **WHEN** frontend sends audio in `audio/webm` format (Chrome/Firefox)
- **THEN** Whisper API processes the file successfully

#### Scenario: MP4 format

- **WHEN** frontend sends audio in `audio/mp4` format (Safari)
- **THEN** Whisper API processes the file successfully

#### Scenario: WAV format fallback

- **WHEN** frontend sends audio in `audio/wav` format
- **THEN** Whisper API processes the file successfully

### Requirement: Error Response

The backend SHALL return appropriate error responses for transcription failures.

#### Scenario: Whisper API error response

- **WHEN** Whisper API fails with error
- **THEN** the system emits SSE error event with `{"message": "Speech recognition failed: <error_detail>", "code": "STT_FAILED"}`

#### Scenario: Invalid audio file

- **WHEN** uploaded file is not a valid audio file
- **THEN** the system returns HTTP 400 with error message before attempting Whisper API call

#### Scenario: Missing OPENAI_API_KEY

- **WHEN** backend starts without OPENAI_API_KEY configured
- **THEN** the system logs error and returns HTTP 500 on first transcription attempt

### Requirement: Transcription Performance

The backend SHALL complete transcription within acceptable latency for conversational UX.

#### Scenario: Fast transcription

- **WHEN** backend receives 10-second audio file
- **THEN** Whisper API returns transcription within 500ms (target: 200-400ms)

#### Scenario: Transcription progress indicator

- **WHEN** transcription is in progress
- **THEN** frontend displays "🎤 轉錄中..." placeholder while waiting for transcription event

### Requirement: Audio File Cleanup

The backend SHALL not persist audio files after transcription completes.

#### Scenario: In-memory processing

- **WHEN** backend receives audio upload
- **THEN** the system processes audio bytes in memory without writing to disk

#### Scenario: Memory cleanup after transcription

- **WHEN** transcription completes or fails
- **THEN** the system releases audio bytes from memory immediately
