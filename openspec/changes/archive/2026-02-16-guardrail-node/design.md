## Context

The Speak app uses a LangGraph workflow to handle chat conversations. Currently, the workflow starts with a `dispatch_node` that fans out to parallel `chat_node` and `correction_node` execution. There is no input filtering - any user request is processed, including off-topic tasks like code generation or math problems.

The app is designed for English conversation practice. Users should be able to discuss any topic conversationally, but should not be able to use the AI as a general-purpose assistant for task execution.

## Goals / Non-Goals

**Goals:**
- Filter user messages that request task execution (code writing, translation, math, etc.)
- Allow all conversational topics, including technical discussions
- Provide friendly, redirecting responses when rejecting requests
- Maintain TTS functionality for rejection messages
- Minimize latency impact (use fast, cheap model)

**Non-Goals:**
- Content moderation (profanity, harmful content) - out of scope
- Rate limiting or abuse prevention
- Modifying existing chat/correction node behavior

## Decisions

### 1. Model Selection: Claude Haiku

**Decision**: Use `claude-haiku-4-5-20251001` for the guardrail node.

**Rationale**:
- Classification is a simple task suitable for smaller models
- Haiku is ~10x cheaper and ~3x faster than Sonnet
- Alternatives considered:
  - Sonnet: Overkill for classification, adds unnecessary latency/cost
  - Rule-based: Too brittle for natural language variations

### 2. Single LLM Call for Classification + Response

**Decision**: One LLM call returns both the classification decision and rejection message.

**Rationale**:
- Reduces latency (one round-trip vs two)
- Response is contextual to the specific request
- Output is structured JSON: `{ "passed": bool, "response": string | null }`

### 3. Remove dispatch_node, Guardrail Does Fan-out

**Decision**: Replace `dispatch_node` with `guardrail_node` as entry point.

**Rationale**:
- `dispatch_node` is a no-op pass-through
- Guardrail needs to be first anyway
- Conditional routing naturally handles fan-out
- Graph structure from summary:
  ```
  START → guardrail → [pass] → chat → tts → END
                    ↘       ↘ correction → END
                    → [reject] → tts → END
  ```

### 4. Rejection Messages Route to TTS

**Decision**: When guardrail rejects, add rejection as AIMessage and route to `tts_node`.

**Rationale**:
- Consistent UX: all AI responses have audio
- `tts_node` already handles reading last AI message
- No TTS code changes needed

### 5. Loose Rejection Policy

**Decision**: Only reject explicit task requests, allow all discussion topics.

**Rationale**:
- "I'm learning Python" ✅ (sharing experience)
- "Write me a Python function" ❌ (task request)
- Key distinction: talking ABOUT something vs asking to DO something

## Risks / Trade-offs

**[Latency]** Adds ~100-150ms for Haiku classification
→ Mitigation: Acceptable for the protection it provides; Haiku is among fastest models

**[False Positives]** May incorrectly reject edge cases
→ Mitigation: Loose policy, prioritize allowing conversation; can tune prompt over time

**[False Negatives]** May miss clever task requests
→ Mitigation: Acceptable trade-off; strict filtering would hurt UX more than occasional leakage

**[State Complexity]** Adding `guardrail_passed` field
→ Mitigation: Simple boolean, minimal complexity; alternative of checking message count is fragile
