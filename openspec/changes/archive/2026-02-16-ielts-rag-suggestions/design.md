## Context

The Speak application provides grammar corrections via the `/summary` endpoint. Users preparing for IELTS exams would benefit from vocabulary suggestions based on the official IELTS word list (approximately 5000 words).

Current flow: User sentences → corrections → tips → common_patterns

New flow adds: corrections → IELTS RAG pipeline → vocabulary suggestions

## Goals / Non-Goals

**Goals:**
- Provide IELTS vocabulary suggestions in `/summary` response
- Ensure all suggested words come from official IELTS word list
- Keep latency acceptable by running RAG pipeline in parallel with existing tips generation
- Support graceful degradation (no suggestions if RAG fails)

**Non-Goals:**
- Real-time vocabulary suggestions during chat (only at summary time)
- User-customizable vocabulary lists
- Caching of RAG results (can be added later if needed)
- Support for other vocabulary lists (TOEFL, GRE, etc.)

## Decisions

### 1. Input Source: Use Corrected Sentences
**Decision**: Process `corrected` sentences, not `original` sentences.
**Rationale**: Original sentences may have grammar errors that affect embedding quality and semantic analysis.
**Alternatives**: Using original sentences would preserve user intent but introduces noise.

### 2. Vector Store: FAISS In-Memory
**Decision**: Use FAISS for vector similarity search, loaded into memory at server startup.
**Rationale**: 5000 words is small enough for in-memory storage (~100ms load time). FAISS provides fast similarity search without external dependencies.
**Alternatives**:
- Pinecone/Weaviate: Overkill for this scale, adds external dependency
- SQLite with vector extension: Slower for similarity search

### 3. Embedding Model: AWS Bedrock Titan
**Decision**: Use Titan Embedding via AWS Bedrock.
**Rationale**: Already using AWS infrastructure, consistent with existing architecture.
**Alternatives**: OpenAI embeddings would require additional API key management.

### 4. LLM Strategy: Haiku for Extraction, Sonnet for Generation
**Decision**:
- Keyword extraction: Claude Haiku (fast, cheap, simple task)
- Suggestion generation: Claude Sonnet (better language understanding)
**Rationale**: Cost optimization - extraction is a simple task that doesn't need Sonnet's capabilities.

### 5. Trigger: Real-time on Each Summary Call
**Decision**: Run RAG pipeline on every `/summary` request with corrections.
**Rationale**: Simple, stateless, no additional infrastructure needed.
**Alternatives**: Background job would add complexity without clear benefit at current scale.

### 6. Index Lifecycle: Pre-built Index
**Decision**: Build FAISS index once via script, load at server startup.
**Rationale**: IELTS word list is static. Rebuilding per-request is wasteful.

## Risks / Trade-offs

**[Latency Impact]** → Run RAG pipeline in parallel with existing tips generation. Set timeout to fail gracefully.

**[Bedrock Rate Limits]** → Monitor usage. Can add caching layer if limits become an issue.

**[Index File Deployment]** → Include pre-built index in repository or build during deployment. Initial implementation: include in repo for simplicity.

**[Empty Suggestions]** → If no relevant IELTS words found, return empty array rather than low-quality suggestions.
