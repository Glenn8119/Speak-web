## ADDED Requirements

### Requirement: Thread-Based State Management

The system SHALL use LangGraph's thread-based state management to persist conversation history and corrections across user sessions.

#### Scenario: Thread creation on first message

- **WHEN** user sends their first message without a thread_id
- **THEN** system generates a new unique thread_id and initializes thread state

#### Scenario: Thread continuation

- **WHEN** user sends a message with an existing thread_id
- **THEN** system retrieves and updates the existing thread state

---

### Requirement: Thread ID Generation

The system SHALL generate unique thread IDs on the backend for new conversations.

#### Scenario: New conversation

- **WHEN** backend receives a message without thread_id
- **THEN** system generates a unique thread*id (e.g., "thread*" + UUID)

#### Scenario: Thread ID returned to frontend

- **WHEN** new thread is created
- **THEN** system includes thread_id in the first SSE event to frontend

---

### Requirement: Frontend Thread ID Storage

The system SHALL enable frontend to store and persist thread_id across page refreshes using localStorage.

#### Scenario: First response received

- **WHEN** frontend receives thread_id from backend
- **THEN** frontend stores thread_id in both application state and localStorage

#### Scenario: Page refresh

- **WHEN** user refreshes the page
- **THEN** frontend retrieves thread_id from localStorage and includes it in subsequent requests

---

### Requirement: Conversation History Persistence

The system SHALL persist complete conversation history (messages and corrections) in thread state.

#### Scenario: Message storage

- **WHEN** user sends a message or AI responds
- **THEN** system appends message to thread state's messages array

#### Scenario: Correction storage

- **WHEN** correction is generated
- **THEN** system appends correction to thread state's corrections array

---

### Requirement: State Survival Across Refresh

The system SHALL ensure conversation state survives page refresh and browser restart.

#### Scenario: Page refresh with thread_id

- **WHEN** user refreshes page and frontend sends thread_id
- **THEN** system retrieves full conversation history from thread state

#### Scenario: Browser restart

- **WHEN** user closes and reopens browser, then visits app
- **THEN** conversation history is available if thread_id is in localStorage

---

### Requirement: New Conversation Reset

The system SHALL allow users to start a new conversation, clearing the current thread_id.

#### Scenario: New Conversation button clicked

- **WHEN** user clicks "New Conversation" button
- **THEN** frontend clears thread_id from state and localStorage

#### Scenario: First message after reset

- **WHEN** user sends message after clearing thread_id
- **THEN** system creates a new thread with fresh state

---

### Requirement: Thread State Schema

The system SHALL maintain thread state with messages array, corrections array, and thread_id.

#### Scenario: State structure

- **WHEN** thread state is created or updated
- **THEN** state contains: messages (array), corrections (array), thread_id (string)

#### Scenario: Message object structure

- **WHEN** message is stored in state
- **THEN** message contains: role (user/assistant), content (string), timestamp (string)

#### Scenario: Correction object structure

- **WHEN** correction is stored in state
- **THEN** correction contains: original, corrected, issues (array), explanation, message_id

---

### Requirement: Checkpointer Configuration

The system SHALL use LangGraph checkpointer for thread persistence with environment-appropriate storage backend.

#### Scenario: Development environment

- **WHEN** system runs in development mode
- **THEN** system uses MemorySaver checkpointer for simplicity

#### Scenario: Production environment

- **WHEN** system runs in production mode
- **THEN** system uses Redis or PostgreSQL checkpointer for durable persistence

---

### Requirement: Thread Lifecycle

The system SHALL persist threads indefinitely until user explicitly starts a new conversation.

#### Scenario: Long-term persistence

- **WHEN** user returns to app days later with same thread_id
- **THEN** system retrieves full conversation history from thread state

#### Scenario: Explicit reset only

- **WHEN** user has not clicked "New Conversation"
- **THEN** thread remains active regardless of time elapsed

---

### Requirement: Thread State Query

The system SHALL allow querying thread state for specific data (e.g., all corrections for summary generation).

#### Scenario: Summary generation query

- **WHEN** summary endpoint is called with thread_id
- **THEN** system retrieves corrections array from thread state

#### Scenario: Conversation history query

- **WHEN** frontend requests conversation history
- **THEN** system retrieves messages array from thread state
