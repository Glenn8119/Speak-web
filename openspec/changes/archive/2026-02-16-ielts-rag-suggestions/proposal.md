## Why

Users practicing English want to expand their vocabulary for IELTS preparation. Currently, the `/summary` endpoint provides grammar corrections but doesn't help users learn more advanced vocabulary alternatives from the official IELTS word list.

## What Changes

- Add new `ielts_suggestions` field to `/summary` response with vocabulary replacement suggestions
- Implement RAG pipeline: keyword extraction (Haiku) → FAISS vector search (5000 IELTS words) → suggestion generation (Sonnet)
- Pre-build FAISS index with Titan Embeddings for fast vocabulary lookup
- Skip IELTS suggestions when no corrections exist (nothing to improve)

## Capabilities

### New Capabilities

- `ielts-rag`: RAG pipeline for suggesting IELTS vocabulary replacements based on corrected sentences

### Modified Capabilities

- `summary-endpoint`: Add `ielts_suggestions` field to response schema (extends existing `/summary` behavior)

## Impact

**New Files**:
- `backend/ielts_rag.py` - RAG pipeline logic (keyword extraction, vector search, suggestion generation)
- `backend/scripts/build_ielts_index.py` - One-time script to build FAISS index
- `backend/data/ielts.faiss` - Pre-built FAISS index
- `backend/data/ielts_metadata.json` - Word metadata (word, definition, example)

**Modified Files**:
- `backend/endpoints/chat.py` - Integrate IELTS RAG in `/summary` endpoint
- `backend/schemas/chat.py` - Add `IELTSSuggestion`, `WordSuggestion` schemas
- `backend/dependencies.py` - FAISS index dependency injection

**Dependencies**:
- AWS Bedrock (Titan Embedding model)
- FAISS library
- IELTS.json word list (5000 words)
