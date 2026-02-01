## general response

1. we don't stream tokens, both chat node and correction node stream result, we use "update" as stream mode, in the future, we'll add a third node for streaming realtime voice response after the chat node, but we can ignore the third node for now.

2. The thread_id is generated in the backend, the frontend will only store it after the first response

## 🤔 Interesting Design Questions

1. Thread Lifecycle Management
   The session persists forever unless the user creates a new conversation (Remember we have a "New Conversation" button)

2. Parallel Execution Timing
   Yes, we show loading state for both

3. As I said in General Response 1, we don't stream token, we only stream the result to the frontend when graph state "update"
