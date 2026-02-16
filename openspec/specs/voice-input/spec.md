## ADDED Requirements

### Requirement: Speech Recognition Initialization

The system SHALL initialize Web Speech API speech recognition when the chat input component mounts.

#### Scenario: Successful initialization in supported browser

- **WHEN** the chat input component mounts in Chrome, Firefox, or Edge
- **THEN** the system creates a SpeechRecognition instance with language set to 'en-US'

#### Scenario: Initialization in unsupported browser

- **WHEN** the chat input component mounts in a browser without Web Speech API support
- **THEN** the system displays an error message and disables the microphone button

### Requirement: Start Voice Recording

The system SHALL allow users to start voice recording by clicking a microphone button.

#### Scenario: User starts recording

- **WHEN** user clicks the microphone button
- **THEN** the system starts speech recognition and updates UI to show recording state

#### Scenario: Recording already in progress

- **WHEN** user clicks the microphone button while already recording
- **THEN** the system stops the current recording

### Requirement: Real-time Transcript Display

The system SHALL display interim speech recognition results in real-time as the user speaks.

#### Scenario: Interim results received

- **WHEN** speech recognition produces interim results
- **THEN** the system updates the chat input field with the interim transcript

#### Scenario: Final results received

- **WHEN** speech recognition produces final results
- **THEN** the system updates the chat input field with the final transcript and stops recording

### Requirement: Voice Input Submission

The system SHALL automatically submit the transcribed text as a chat message when speech recognition completes.

#### Scenario: Speech recognition completes successfully

- **WHEN** speech recognition produces a final transcript
- **THEN** the system sends the transcript as a chat message via the existing SSE endpoint

#### Scenario: Empty transcript

- **WHEN** speech recognition completes with an empty transcript
- **THEN** the system does NOT send a message and clears the recording state

### Requirement: Speech Recognition Error Handling

The system SHALL handle speech recognition errors gracefully without blocking the text input fallback.

#### Scenario: Recognition error occurs

- **WHEN** speech recognition encounters an error (network, no-speech, aborted)
- **THEN** the system logs the error, displays a user-friendly message, and stops recording

#### Scenario: Recognition timeout

- **WHEN** no speech is detected within the timeout period
- **THEN** the system stops recording and clears the input field

### Requirement: Text Input Fallback

The system SHALL maintain text input as the primary input method alongside voice input.

#### Scenario: User types while voice input is available

- **WHEN** user types in the chat input field
- **THEN** the system accepts typed input normally, regardless of voice input availability

#### Scenario: User switches between voice and text

- **WHEN** user starts typing after using voice input
- **THEN** the system clears any interim voice transcript and accepts the typed text
