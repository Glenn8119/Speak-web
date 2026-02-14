## 1. State Changes

- [ ] 1.1 Add `guardrail_passed: bool` field to `GraphState` TypedDict in `backend/graph.py`

## 2. Guardrail Node Implementation

- [ ] 2.1 Create `guardrail_node` function in `backend/graph.py`
- [ ] 2.2 Implement intent classification prompt with JSON output schema
- [ ] 2.3 Parse LLM response and set `guardrail_passed` accordingly
- [ ] 2.4 Return rejection message as `AIMessage` when guardrail rejects

## 3. Graph Structure Changes

- [ ] 3.1 Add `guardrail_node` to workflow in `create_workflow()`
- [ ] 3.2 Remove `dispatch_node` from workflow
- [ ] 3.3 Set `guardrail_node` as entry point instead of `dispatch_node`
- [ ] 3.4 Create `route_after_guardrail` conditional routing function
- [ ] 3.5 Add conditional edges: pass → [chat, correction], reject → tts

## 4. Testing

- [ ] 4.1 Test conversational messages pass through to chat/correction
- [ ] 4.2 Test task requests are rejected with friendly message
- [ ] 4.3 Test rejection messages have TTS audio generated
