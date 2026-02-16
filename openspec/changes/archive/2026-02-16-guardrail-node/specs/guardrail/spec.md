## ADDED Requirements

### Requirement: Guardrail classifies user intent
The system SHALL classify each user message as either conversational (pass) or task-requesting (reject) before processing.

#### Scenario: User discusses a topic conversationally
- **WHEN** user sends "I'm learning Python and it's really fun"
- **THEN** guardrail_passed is set to true
- **AND** message is routed to chat_node and correction_node

#### Scenario: User asks for opinion on a topic
- **WHEN** user sends "Do you think AI will change the world?"
- **THEN** guardrail_passed is set to true
- **AND** message is routed to chat_node and correction_node

#### Scenario: User requests code generation
- **WHEN** user sends "Write me a Python function to sort a list"
- **THEN** guardrail_passed is set to false
- **AND** a friendly rejection AIMessage is added to state

#### Scenario: User requests translation
- **WHEN** user sends "Translate this paragraph to Chinese"
- **THEN** guardrail_passed is set to false
- **AND** a friendly rejection AIMessage is added to state

### Requirement: Rejection messages are friendly and redirecting
The system SHALL generate contextual rejection messages that acknowledge the request and redirect to conversation topics.

#### Scenario: Rejection message tone
- **WHEN** guardrail rejects a user message
- **THEN** the rejection message is warm and encouraging
- **AND** the message suggests returning to conversation practice

#### Scenario: Rejection message is contextual
- **WHEN** user asks to write code
- **THEN** rejection message acknowledges their interest in coding
- **AND** suggests discussing coding experiences instead

### Requirement: Rejection messages have TTS audio
The system SHALL route rejected messages to tts_node to generate audio response.

#### Scenario: Rejected request gets audio
- **WHEN** guardrail rejects a user message
- **THEN** the workflow routes to tts_node
- **AND** tts_node generates audio for the rejection message

### Requirement: Guardrail uses Claude Haiku
The system SHALL use claude-haiku-4-5-20251001 model for guardrail classification.

#### Scenario: Model configuration
- **WHEN** guardrail_node processes a message
- **THEN** it invokes claude-haiku-4-5-20251001
- **AND** uses temperature 0.3 for consistent classification

### Requirement: GraphState includes guardrail_passed field
The system SHALL add a guardrail_passed boolean field to GraphState.

#### Scenario: State tracks guardrail result
- **WHEN** guardrail_node completes
- **THEN** state contains guardrail_passed boolean
- **AND** subsequent routing uses this field
