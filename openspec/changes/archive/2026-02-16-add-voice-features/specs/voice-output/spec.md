## ADDED Requirements

### Requirement: TTS Node Integration

The system SHALL add a TTS node to the LangGraph workflow that executes in series after the chat node completes.

#### Scenario: Chat response completes

- **WHEN** the chat node produces a complete AI response
- **THEN** the system invokes the TTS node with the chat response text

#### Scenario: TTS node receives empty response

- **WHEN** the chat node produces an empty or null response
- **THEN** the TTS node skips audio generation and completes immediately

### Requirement: OpenAI TTS Conversion

The system SHALL convert AI chat responses to speech using OpenAI TTS API with model 'tts-1', voice 'nova', and format 'opus'.

#### Scenario: Successful TTS conversion

- **WHEN** the TTS node receives a chat response text
- **THEN** the system calls OpenAI TTS API and receives Opus-encoded audio data

#### Scenario: TTS API error

- **WHEN** the OpenAI TTS API returns an error
- **THEN** the system logs the error and completes without audio (text response still delivered)

#### Scenario: TTS API timeout

- **WHEN** the OpenAI TTS API request times out
- **THEN** the system logs the timeout and completes without audio

### Requirement: Audio Data Encoding

The system SHALL encode the TTS audio data as base64 for transmission via SSE.

#### Scenario: Audio data received from OpenAI

- **WHEN** the TTS node receives Opus audio bytes from OpenAI
- **THEN** the system encodes the audio as base64 string

### Requirement: SSE Audio Streaming

The system SHALL stream audio data to the frontend via a new 'audio_chunk' SSE event.

#### Scenario: TTS conversion completes

- **WHEN** the TTS node completes audio encoding
- **THEN** the system sends an 'audio_chunk' SSE event with base64 audio and format 'opus'

#### Scenario: Multiple messages in same thread

- **WHEN** multiple chat messages are sent in the same thread
- **THEN** each message receives its own audio_chunk event with corresponding audio

### Requirement: Frontend Audio Playback

The system SHALL decode and play Opus audio using Web Audio API when receiving audio_chunk events.

#### Scenario: Audio chunk event received

- **WHEN** the frontend receives an 'audio_chunk' SSE event
- **THEN** the system decodes the base64 audio to ArrayBuffer and plays it via AudioContext

#### Scenario: Audio decode failure

- **WHEN** audio decoding fails (invalid data, unsupported format)
- **THEN** the system logs the error and does NOT block text display

#### Scenario: AudioContext suspended

- **WHEN** AudioContext is in suspended state (browser autoplay policy)
- **THEN** the system attempts to resume AudioContext on user interaction

### Requirement: Audio Playback Timing

The system SHALL play audio automatically after the chat response text is displayed, without requiring user interaction.

#### Scenario: Text and audio both ready

- **WHEN** chat response text is displayed and audio chunk is received
- **THEN** the system plays audio immediately without waiting for user action

### Requirement: No Audio UI Controls

The system SHALL play audio automatically without displaying playback controls (pause, replay, progress bar).

#### Scenario: Audio playback starts

- **WHEN** the system starts playing audio
- **THEN** no visual playback controls are displayed to the user

#### Scenario: User wants to replay audio

- **WHEN** audio playback completes
- **THEN** the system does NOT provide a replay button

### Requirement: Graph State Management

The system SHALL NOT store full audio data in LangGraph state to avoid bloating thread persistence.

#### Scenario: TTS node completes

- **WHEN** the TTS node generates audio
- **THEN** the system streams audio via SSE but does NOT add audio bytes to graph state

#### Scenario: Thread checkpoint saved

- **WHEN** LangGraph saves a checkpoint after TTS node
- **THEN** the checkpoint does NOT include audio data (only message text)
