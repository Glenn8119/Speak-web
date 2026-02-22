## ADDED Requirements

### Requirement: On-Demand Summary Generation

The system SHALL generate practice summaries when user clicks the Summary button, regardless of conversation length or state.

#### Scenario: Summary requested mid-conversation

- **WHEN** user clicks Summary button during an active conversation
- **THEN** system generates summary based on all corrections accumulated so far

#### Scenario: Summary requested after multiple messages

- **WHEN** user has sent 10+ messages and clicks Summary button
- **THEN** system generates comprehensive summary covering all corrections

#### Scenario: Summary requested with no corrections

- **WHEN** user clicks Summary button but no grammar errors have been found
- **THEN** system returns encouraging message indicating excellent grammar

---

### Requirement: Two-Part Summary Structure

The system SHALL generate summaries with two distinct parts: correction list (no AI) and practice tips (AI-generated).

#### Scenario: Part 1 - Correction list

- **WHEN** summary is generated
- **THEN** Part 1 contains complete list of all corrections from thread state without AI processing

#### Scenario: Part 2 - AI tips

- **WHEN** summary is generated
- **THEN** Part 2 contains AI-generated tips, common patterns, and practice suggestions based on correction analysis

---

### Requirement: Correction List Retrieval

The system SHALL retrieve all corrections from the conversation thread state without requiring additional AI calls.

#### Scenario: Query thread state

- **WHEN** Part 1 of summary is generated
- **THEN** system queries LangGraph thread state for corrections array

#### Scenario: Chronological order

- **WHEN** corrections are listed
- **THEN** corrections appear in chronological order (oldest to newest)

---

### Requirement: AI-Generated Practice Tips

The system SHALL use AI to analyze accumulated corrections and provide personalized learning tips and practice suggestions.

#### Scenario: Pattern identification

- **WHEN** AI analyzes corrections for Part 2
- **THEN** output identifies common error patterns (e.g., "Past tense errors: 3 occurrences")

#### Scenario: Practice suggestions

- **WHEN** AI generates tips
- **THEN** output includes 2-3 specific practice exercises or focus areas

#### Scenario: Encouraging tone

- **WHEN** summary is generated
- **THEN** AI tips use positive, motivational language

---

### Requirement: Common Pattern Analysis

The system SHALL identify and highlight frequently occurring grammar patterns in the user's corrections.

#### Scenario: Repeated error type

- **WHEN** user makes the same type of error multiple times (e.g., past tense)
- **THEN** summary highlights this as a common pattern with frequency count

#### Scenario: Diverse errors

- **WHEN** user makes various different error types
- **THEN** summary lists patterns without over-emphasizing any single one

---

### Requirement: Summary Response Format

The system SHALL return summaries as structured JSON containing corrections array and tips string.

#### Scenario: Structured output

- **WHEN** summary is generated
- **THEN** response includes fields: corrections (array), tips (string)

---

### Requirement: Request-Response Model

The system SHALL use standard HTTP request-response for summary generation, not streaming.

#### Scenario: Summary endpoint

- **WHEN** user requests summary
- **THEN** system processes request and returns complete summary in single HTTP response

#### Scenario: Thread ID requirement

- **WHEN** summary is requested
- **THEN** request MUST include thread_id to identify which conversation to summarize

---

### Requirement: Future Notion Integration Placeholder

The system SHALL include a TODO comment for future Notion MCP sync integration in the summary endpoint.

#### Scenario: Code documentation

- **WHEN** summary endpoint is implemented
- **THEN** code includes TODO comment indicating future Notion MCP sync feature
