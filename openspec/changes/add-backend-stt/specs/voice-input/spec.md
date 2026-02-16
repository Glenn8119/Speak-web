## MODIFIED Requirements

### Requirement: Start Voice Recording

The system SHALL allow users to start voice recording by clicking a microphone button in toggle mode.

#### Scenario: User starts recording

- **WHEN** user clicks the microphone button while not recording
- **THEN** the system starts audio recording using MediaRecorder API and updates UI to show "⏹️ 停止並送出"

#### Scenario: User stops recording

- **WHEN** user clicks the microphone button while recording
- **THEN** the system stops recording, uploads the audio file to backend, and displays "🎤 轉錄中..."

### Requirement: Real-time Transcript Display

The system SHALL display the transcribed text received from the backend immediately upon transcription completion.

#### Scenario: Transcription received from backend

- **WHEN** backend returns transcription via SSE `transcription` event
- **THEN** the system updates the user message with the transcribed text and removes the "轉錄中..." placeholder

#### Scenario: Transcription displays punctuation

- **WHEN** backend returns transcription with punctuation and capitalization
- **THEN** the system displays the text exactly as received, preserving all punctuation and capitalization

### Requirement: Speech Recognition Error Handling

The system SHALL handle audio recording and transcription errors gracefully without blocking the text input fallback.

#### Scenario: Microphone permission denied

- **WHEN** user denies microphone permission
- **THEN** the system displays an error message and keeps the microphone button visible for retry

#### Scenario: Backend transcription error

- **WHEN** backend returns an error during transcription
- **THEN** the system displays a user-friendly error message and allows user to retry recording

#### Scenario: Network error during upload

- **WHEN** audio upload fails due to network error
- **THEN** the system displays an error message and allows user to retry recording

## REMOVED Requirements

### Requirement: Speech Recognition Initialization

**Reason**: No longer using Web Speech API, now using MediaRecorder API which doesn't require initialization

**Migration**: Remove `useSpeechRecognition` hook and replace with `useAudioRecorder` hook

### Requirement: Voice Input Submission

**Reason**: Voice input is now handled by backend after transcription, not automatically submitted on recognition complete

**Migration**: Audio is uploaded to backend which handles transcription and then feeds into existing chat flow

## ADDED Requirements

### Requirement: Audio Recording with Toggle Mode

The system SHALL record audio using MediaRecorder API with click-to-toggle interaction.

#### Scenario: First click starts recording

- **WHEN** user clicks the microphone button for the first time
- **THEN** the system requests microphone permission (if not granted), starts MediaRecorder, and changes button to "⏹️ 停止並送出"

#### Scenario: Second click stops and submits

- **WHEN** user clicks the button again while recording
- **THEN** the system stops MediaRecorder, creates audio blob, and uploads to backend `/chat` endpoint

### Requirement: Audio Format Detection

The system SHALL detect and use the best supported audio format for the user's browser.

#### Scenario: Chrome/Firefox browser

- **WHEN** user is on Chrome or Firefox
- **THEN** the system uses `audio/webm;codecs=opus` format for optimal compression

#### Scenario: Safari browser

- **WHEN** user is on Safari
- **THEN** the system falls back to `audio/mp4` format

#### Scenario: Unsupported format

- **WHEN** none of the preferred formats are supported
- **THEN** the system uses `audio/wav` as final fallback

### Requirement: Audio Upload

The system SHALL upload recorded audio to the backend `/chat` endpoint as multipart/form-data.

#### Scenario: Successful upload

- **WHEN** user stops recording
- **THEN** the system creates a FormData with the audio blob and current thread_id, sends POST request to `/chat`

#### Scenario: Upload with placeholder message

- **WHEN** audio upload starts
- **THEN** the system creates a placeholder user message showing "🎤 轉錄中..." while waiting for transcription

### Requirement: Recording State Persistence

The system SHALL maintain clear visual feedback of recording state throughout the recording session.

#### Scenario: Recording indicator visible

- **WHEN** recording is in progress
- **THEN** the microphone button displays "⏹️ 停止並送出" and has a distinct visual style (e.g., red background or pulsing animation)

#### Scenario: Recording state survives component updates

- **WHEN** React re-renders during recording
- **THEN** the recording state and MediaRecorder instance persist without interruption
