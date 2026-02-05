## 1. Project Setup

- [x] 1.1 Create project directory structure (frontend/, backend/)
- [x] 1.2 Initialize backend with FastAPI and create requirements.txt
- [x] 1.3 Initialize frontend with React + Vite
- [x] 1.4 Set up environment variables (.env) for Anthropic API key
- [x] 1.5 Create .gitignore for both frontend and backend
- [x] 1.6 Install LangGraph and Anthropic SDK in backend
- [x] 1.7 Install SSE client library in frontend

## 2. Backend - LangGraph Workflow

- [x] 2.1 Define GraphState TypedDict with messages, corrections, and thread_id
- [x] 2.2 Implement chat_node function with conversational prompt
- [x] 2.3 Implement correction_node function with grammar checking prompt
- [x] 2.4 Create dispatch node for parallel execution entry point
- [x] 2.5 Build LangGraph workflow with parallel edges
- [x] 2.6 Configure MemorySaver checkpointer for development
- [x] 2.7 Compile graph with checkpointer
- [x] 2.8 Test graph execution with sample inputs

## 3. Backend - API Endpoints

- [x] 3.1 Create FastAPI app instance
- [x] 3.2 Implement POST /chat endpoint with SSE streaming
- [x] 3.3 Add thread_id generation logic for new conversations
- [x] 3.4 Implement SSE event generator for graph updates
- [x] 3.5 Add error handling for node failures in stream
- [x] 3.6 Implement POST /summary endpoint
- [x] 3.7 Add thread state query logic for corrections retrieval
- [x] 3.8 Implement AI-powered tips generation for summary Part 2
- [x] 3.9 Add TODO comment for future Notion MCP sync
- [x] 3.10 Add CORS middleware for frontend communication

## 4. Backend - Prompt Engineering

- [x] 4.1 Refine chat node system prompt for natural conversation
- [x] 4.2 Refine correction node system prompt for grammar focus
- [x] 4.3 Add examples to correction prompt for consistency
- [x] 4.4 Refine summary tips prompt for encouraging tone
- [x] 4.5 Test prompts with various user inputs and iterate

## 5. Frontend - Project Structure

- [x] 5.1 Create components directory structure
- [x] 5.2 Create hooks directory for custom hooks
- [x] 5.3 Set up state management (Context or Zustand)
- [x] 5.4 Create types/interfaces for Message and Correction

## 6. Frontend - Core Components

- [x] 6.1 Create ChatMessage component for displaying messages
- [x] 6.2 Create CorrectionAccordion component with expand/collapse
- [x] 6.3 Create MessageInput component for user text input
- [x] 6.4 Create ChatContainer component to hold conversation
- [x] 6.5 Create LoadingIndicator component for chat and correction
- [x] 6.6 Create SummaryModal component for displaying summaries
- [x] 6.7 Create NewConversationButton component

## 7. Frontend - SSE Integration

- [x] 7.1 Create useSSE custom hook for EventSource management
- [x] 7.2 Implement SSE event handlers for different event types
- [x] 7.3 Add thread_id event handler to store in state and localStorage
- [x] 7.4 Add chat_response event handler to update messages
- [x] 7.5 Add correction event handler to attach to user messages
- [x] 7.6 Add error event handler for node failures
- [x] 7.7 Implement automatic reconnection logic

## 8. Frontend - State Management

- [x] 8.1 Create ChatContext with messages, threadId, and loading states
- [x] 8.2 Implement addMessage action
- [x] 8.3 Implement attachCorrection action
- [x] 8.4 Implement setThreadId action with localStorage sync
- [x] 8.5 Implement clearThread action for new conversation
- [x] 8.6 Implement loading state management for chat and correction

## 9. Frontend - Chat Interface

- [x] 9.1 Build main App component with ChatContainer
- [x] 9.2 Implement message sending flow (input → SSE request)
- [x] 9.3 Add loading states display for both chat and correction
- [x] 9.4 Implement accordion toggle for corrections
- [x] 9.5 Add New Conversation button with confirmation
- [x] 9.6 Add Summary button to trigger summary modal
- [x] 9.7 Style chat interface with modern, clean design

## 10. Frontend - Summary Feature

- [x] 10.1 Implement summary request to POST /summary endpoint
- [x] 10.2 Create summary modal UI with two sections (corrections + tips)
- [x] 10.3 Display corrections list in Part 1
- [x] 10.4 Display AI tips and common patterns in Part 2
- [x] 10.5 Add close button and modal overlay
- [x] 10.6 Handle empty summary case (no corrections)

## 11. Frontend - Thread Persistence

- [x] 11.1 Implement localStorage read on app initialization
- [x] 11.2 Load existing thread_id from localStorage if present
- [x] 11.3 Test page refresh with active conversation
- [x] 11.4 Test browser restart with localStorage persistence
- [x] 11.5 Implement thread_id clearing on new conversation

## 12. Error Handling

- [ ] 12.1 Add backend error logging for node failures
- [ ] 12.2 Implement frontend error display for SSE failures
- [ ] 12.3 Add retry logic for failed SSE connections
- [ ] 12.4 Handle partial failures (one node succeeds, one fails)
- [ ] 12.5 Add user-friendly error messages
- [ ] 12.6 Test error scenarios (network drop, API failure, etc.)

## 13. Testing & Validation

- [ ] 13.1 Test parallel node execution timing
- [ ] 13.2 Test thread persistence across page refresh
- [ ] 13.3 Test new conversation flow
- [ ] 13.4 Test summary generation with various correction counts
- [ ] 13.5 Test accordion expand/collapse behavior
- [ ] 13.6 Test loading states for both chat and correction
- [ ] 13.7 Validate correction quality with sample inputs
- [ ] 13.8 Test edge cases (empty messages, very long messages, etc.)

## 14. Documentation

- [ ] 14.1 Add README.md with setup instructions
- [ ] 14.2 Document environment variables needed
- [ ] 14.3 Add API endpoint documentation
- [ ] 14.4 Document LangGraph workflow structure
- [ ] 14.5 Add frontend component documentation
- [ ] 14.6 Document deployment considerations

## 15. Polish & Optimization

- [ ] 15.1 Optimize prompt token usage
- [ ] 15.2 Add responsive design for mobile
- [ ] 15.3 Improve UI/UX based on testing feedback
- [ ] 15.4 Add loading animations and transitions
- [ ] 15.5 Optimize SSE connection management
- [ ] 15.6 Review and refactor code for clarity
