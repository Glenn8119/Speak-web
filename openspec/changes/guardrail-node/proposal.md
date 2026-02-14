## Why

The chat endpoint currently has no input filtering. Users can request tasks outside the app's purpose (e.g., writing code, solving math problems, translating text). Adding a guardrail node ensures conversations stay focused on English practice while maintaining a friendly user experience.

## What Changes

- Add `guardrail_node` as the entry point in the LangGraph workflow
- Replace `dispatch_node` with guardrail's built-in fan-out routing
- Use Claude Haiku for fast, cost-effective intent classification
- Generate friendly rejection messages that redirect users to conversation topics
- Add `guardrail_passed` field to `GraphState`

## Capabilities

### New Capabilities
- `guardrail`: Intent classification node that filters inappropriate requests and routes to chat/correction nodes or directly to TTS for rejections

### Modified Capabilities
- None (this is additive; existing chat and correction behavior unchanged)

## Impact

- **Code**: `backend/graph.py` - new node, modified graph structure, state changes
- **API**: No endpoint changes; SSE events remain the same
- **Dependencies**: None new (uses existing langchain_anthropic)
- **Performance**: Adds one Haiku LLM call (~100ms) before chat processing
