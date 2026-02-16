## Context

We are building a web-based English practice application inspired by Speak. The current state is a greenfield project with no existing codebase. The application needs to provide real-time conversational practice with AI-powered grammar feedback.

**Constraints**:

- Text-only interface for initial release (voice streaming planned for future)
- Must work across page refreshes (conversation persistence required)
- Focus on natural, everyday English - not formal writing correction
- Budget-conscious (minimize LLM API calls where possible)

**Stakeholders**:

- English learners seeking accessible practice tools
- Future: Integration with Notion for learning journals

## Goals / Non-Goals

**Goals:**

- Deliver real-time conversational AI with parallel grammar correction
- Provide persistent conversation state across sessions
- Enable on-demand practice summaries with AI-generated tips
- Create a responsive, intuitive UI with hidden-by-default corrections
- Build a scalable architecture that supports future voice streaming

**Non-Goals:**

- Voice input/output (deferred to Phase 2)
- User authentication or multi-user support (single-session focus)
- Formal writing correction or essay grading
- Mobile native apps (web-first approach)
- Real-time collaborative features

## Decisions

### 1. Backend Framework: FastAPI + LangGraph

**Decision**: Use FastAPI for HTTP layer and LangGraph for AI orchestration.

**Rationale**:

- **FastAPI**: Native async support, excellent SSE streaming, fast development
- **LangGraph**: Built-in state management, parallel node execution, Anthropic integration, thread persistence

**Alternatives Considered**:

- **Plain FastAPI + direct Anthropic calls**: Simpler but requires manual state management and parallel execution logic
- **LangChain without LangGraph**: Lacks structured workflow and persistence features
- **Node.js + custom orchestration**: Team familiarity with Python ecosystem favors FastAPI

**Trade-off**: LangGraph adds dependency complexity but provides critical features (persistence, parallel execution) out of the box.

---

### 2. Streaming Strategy: LangGraph `stream_mode="updates"`

**Decision**: Use `stream_mode="updates"` to stream complete node outputs, not token-by-token.

**Rationale**:

- Simpler frontend handling (complete responses vs. partial tokens)
- Cleaner UX for grammar corrections (show complete correction at once)
- Easier error handling (node-level failures vs. mid-stream errors)
- Future voice node will stream audio chunks separately

**Alternatives Considered**:

- **Token-by-token streaming**: More "live" feel but complex state management and correction display
- **No streaming**: Poor UX, users wait for both chat and correction to complete

**Trade-off**: Slightly less "real-time" feel compared to token streaming, but significantly simpler implementation.

---

### 3. LLM Provider: Anthropic Claude

**Decision**: Use Anthropic Claude via LangGraph's `ChatAnthropic`.

**Rationale**:

- Strong performance on conversational and grammar tasks
- Native LangGraph integration
- Competitive pricing for parallel calls
- Team has existing AWS Bedrock experience (can switch to Bedrock Claude if needed)

**Alternatives Considered**:

- **OpenAI GPT-4**: Excellent but more expensive for parallel calls
- **AWS Bedrock**: Adds infrastructure complexity, prefer direct API for MVP
- **Local models**: Insufficient quality for grammar correction

**Trade-off**: API costs vs. quality. Claude provides best balance for this use case.

---

### 4. Parallel Execution: Separate Chat and Correction Nodes

**Decision**: Run chat and correction as independent parallel LangGraph nodes.

**Rationale**:

- Faster response time (whichever finishes first streams immediately)
- Clear separation of concerns (different prompts, different outputs)
- Easier to add future nodes (e.g., voice streaming)
- Simpler error handling (one node can fail without blocking the other)

**Alternatives Considered**:

- **Single node with dual output**: Simpler graph but slower (sequential processing)
- **Single call with structured output**: Cheaper but forces sequential processing and complex prompt engineering

**Trade-off**: Two LLM calls cost more but provide better UX and flexibility.

---

### 5. Thread Persistence: LangGraph Checkpointer

**Decision**: Use LangGraph's checkpointer for thread-based conversation state.

**Rationale**:

- Built-in persistence with minimal code
- Survives page refresh and server restart
- Supports future features (conversation history, analytics)
- Standard pattern for LangGraph applications

**Implementation**:

- **Development**: `MemorySaver` (in-memory, simple setup)
- **Production**: Redis or PostgreSQL (to be decided based on deployment environment)

**Alternatives Considered**:

- **Frontend-only state**: Lost on refresh, no server-side history
- **Custom database**: More work, reinventing LangGraph features
- **Session storage**: Doesn't survive server restart

**Trade-off**: Requires external storage for production, but provides essential persistence.

---

### 6. Frontend Framework: React + Vite

**Decision**: Use React with Vite for the frontend.

**Rationale**:

- Fast development with Vite's HMR
- Rich ecosystem for SSE clients and UI components
- Team familiarity
- Easy to add future features (voice streaming, complex state)

**Alternatives Considered**:

- **Vanilla JS**: Simpler but harder to maintain as features grow
- **Next.js**: Overkill for single-page app, no SSR needed
- **Svelte/Vue**: Less team familiarity

**Trade-off**: React bundle size vs. development speed. Vite mitigates build performance concerns.

---

### 7. Communication Protocol: Server-Sent Events (SSE)

**Decision**: Use SSE for streaming updates from backend to frontend.

**Rationale**:

- Native browser support (EventSource API)
- Simpler than WebSockets for unidirectional streaming
- Works well with FastAPI's `StreamingResponse`
- Automatic reconnection handling

**Alternatives Considered**:

- **WebSockets**: Bidirectional but overkill for this use case
- **Long polling**: Inefficient and complex
- **HTTP/2 Server Push**: Limited browser support

**Trade-off**: Unidirectional only, but that's all we need for this use case.

---

### 8. Correction Display: Accordion UI (Collapsed by Default)

**Decision**: Show corrections as collapsed accordions under user messages.

**Rationale**:

- Reduces visual clutter (corrections are secondary to conversation)
- User controls when to review corrections
- Maintains conversation flow
- Mobile-friendly (less scrolling)

**Alternatives Considered**:

- **Always visible**: Too cluttered, distracts from conversation
- **Separate panel**: Disconnects correction from context
- **Inline highlighting**: Complex to implement, disrupts message display

**Trade-off**: Requires user action to see corrections, but improves overall UX.

---

### 9. Summary Generation: Hybrid Approach (No-AI List + AI Tips)

**Decision**: Part 1 queries thread state (no AI), Part 2 uses AI for tips.

**Rationale**:

- Listing corrections is deterministic (no AI needed, faster, cheaper)
- AI tips add value through pattern recognition and personalized suggestions
- Separates concerns (data retrieval vs. analysis)

**Alternatives Considered**:

- **Full AI summary**: More expensive, slower, unnecessary for simple listing
- **No AI summary**: Less valuable, just shows raw data

**Trade-off**: Hybrid approach balances cost and value.

---

### 10. Project Structure: Monorepo with Separate Frontend/Backend

**Decision**: Single repository with `frontend/` and `backend/` directories.

**Rationale**:

- Easier development (single clone, coordinated changes)
- Shared documentation and configuration
- Simpler deployment for MVP
- Can split later if needed

**Alternatives Considered**:

- **Separate repositories**: More overhead for small team
- **Backend serves frontend**: Couples deployment, harder to scale

**Trade-off**: Monorepo can become unwieldy at scale, but appropriate for MVP.

---

## Risks / Trade-offs

### Risk: Parallel Node Timing Variability

**Description**: Chat and correction nodes may have unpredictable completion times, leading to inconsistent UX.

**Mitigation**:

- Show loading states for both components
- Design UI to handle either-first arrival gracefully
- Monitor node execution times and optimize slower prompts

---

### Risk: LangGraph Thread State Growth

**Description**: Long conversations accumulate large state, slowing down processing and increasing storage costs.

**Mitigation**:

- Implement thread expiration (e.g., 7 days of inactivity)
- Consider state summarization for very long threads
- Monitor thread sizes and add limits if needed

---

### Risk: Checkpointer Choice Locks Us In

**Description**: Starting with MemorySaver, switching to Redis/Postgres later may require migration.

**Mitigation**:

- LangGraph checkpointers use standard interface (switching is straightforward)
- Document checkpointer choice as configuration, not hardcoded
- Plan for migration script if needed

---

### Risk: Single LLM Provider Dependency

**Description**: Relying solely on Anthropic creates vendor lock-in and potential outage risk.

**Mitigation**:

- Use LangGraph's abstraction layer (easy to swap LLM providers)
- Consider fallback to AWS Bedrock Claude if Anthropic API is down
- Monitor API reliability and costs

---

### Risk: SSE Connection Drops

**Description**: Network issues or server restarts can drop SSE connections mid-stream.

**Mitigation**:

- Frontend implements automatic reconnection with EventSource
- Backend ensures thread state is saved before streaming
- Add retry logic for failed requests

---

### Risk: Grammar Correction Quality Variability

**Description**: AI may produce inconsistent or incorrect grammar corrections.

**Mitigation**:

- Carefully engineer correction prompts with examples
- Focus on "natural English" rather than strict rules
- Monitor correction quality and iterate on prompts
- Consider user feedback mechanism for future

---

### Risk: Cost Scaling with Usage

**Description**: Two LLM calls per message (chat + correction) doubles API costs.

**Mitigation**:

- Monitor usage and costs closely
- Consider rate limiting or usage caps for public deployment
- Optimize prompts to reduce token usage
- Evaluate cheaper models for correction node if quality is sufficient

---

## Migration Plan

**N/A** - This is a greenfield project with no existing system to migrate from.

**Deployment Strategy**:

1. Deploy backend with MemorySaver checkpointer for initial testing
2. Deploy frontend to static hosting (Vercel, Netlify, or S3)
3. Test end-to-end with real users
4. Switch to Redis/Postgres checkpointer before production launch
5. Monitor performance and costs

**Rollback Strategy**:

- Backend: Revert to previous Docker image or commit
- Frontend: Revert static deployment
- Data: Thread state is ephemeral (no data loss risk for MVP)

---

## Open Questions

1. **Checkpointer for Production**: Redis (fast, ephemeral) or PostgreSQL (persistent, queryable)?
   - **Decision needed by**: Before production deployment
   - **Depends on**: Deployment environment and persistence requirements

2. **Error Handling for Partial Failures**: If chat succeeds but correction fails, should we:
   - Show chat response with "Correction unavailable" message?
   - Retry correction automatically?
   - Hide correction accordion entirely?
   - **Decision needed by**: During implementation

3. **Thread Expiration Policy**: How long should threads persist?
   - Forever (until "New Conversation")?
   - 7 days of inactivity?
   - 30 days absolute?
   - **Decision needed by**: Before production deployment

4. **Rate Limiting**: Should we implement rate limiting for public deployment?
   - Per IP? Per session?
   - What limits are appropriate?
   - **Decision needed by**: Before public launch

5. **Prompt Engineering**: Final prompts for chat and correction nodes need refinement.
   - **Decision needed by**: During implementation and testing
   - **Approach**: Iterate based on real usage feedback
