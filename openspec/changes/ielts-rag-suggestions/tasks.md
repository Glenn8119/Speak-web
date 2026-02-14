## 1. Dependencies and Setup

- [x] 1.1 Add FAISS and langchain dependencies to pyproject.toml
- [x] 1.2 Create backend/data/ directory for index files
- [x] 1.3 Verify IELTS.json word list exists in project root

## 2. FAISS Index Building

- [x] 2.1 Create backend/scripts/build_ielts_index.py script
- [x] 2.2 Implement Titan Embedding calls for word chunks (amazon.titan-embed-text-v2:0)
- [x] 2.3 Build FAISS index from embeddings
- [x] 2.4 Save index.faiss and index.pkl to backend/data/ielts_index/ (LangChain default format)
- [x] 2.5 Run script to generate index files

## 3. Core RAG Pipeline

- [x] 3.1 Create backend/ielts_rag.py module
- [x] 3.2 Implement keyword extraction function using Claude Haiku
- [x] 3.3 Implement vector search function using FAISS
- [x] 3.4 Implement suggestion generation function using Claude Sonnet
- [x] 3.5 Create main pipeline function that orchestrates all steps

## 4. Schema Updates

- [x] 4.1 Add WordSuggestion schema to backend/schemas/chat.py
- [x] 4.2 Add IELTSSuggestion schema to backend/schemas/chat.py
- [x] 4.3 Update SummaryResponse to include ielts_suggestions field

## 5. Dependency Injection

- [x] 5.1 Add FAISS index loading function to backend/dependencies.py
- [x] 5.2 Implement lifespan handler to load index at server startup
- [x] 5.3 Create get_ielts_index dependency for endpoint injection

## 6. Endpoint Integration

- [x] 6.1 Modify /summary endpoint to accept FAISS index dependency
- [x] 6.2 Integrate IELTS RAG pipeline call in parallel with tips generation
- [x] 6.3 Handle empty corrections case (skip RAG pipeline)
- [x] 6.4 Implement graceful degradation on RAG failure

## 7. Frontend Types

- [x] 7.1 Add WordSuggestion interface to frontend/src/types/index.ts
- [x] 7.2 Update Summary interface to include ielts_suggestions field

## 8. Frontend Components

- [x] 8.1 Create IELTSSuggestions component in frontend/src/components/
- [x] 8.2 Display target word, IELTS word, definition, example, and improved sentence
- [x] 8.3 Style component to match existing SummaryModal design (gray-800 cards, indigo accents)
- [x] 8.4 Handle empty suggestions gracefully (hide section when no suggestions)

## 9. Frontend Integration

- [x] 9.1 Import and add IELTSSuggestions component to SummaryModal
- [x] 9.2 Position IELTS suggestions section between Common Patterns and Practice Tips

## 10. Testing

- [x] 10.1 Verify server starts and loads FAISS index successfully
- [x] 10.2 Test /summary endpoint with corrections returns ielts_suggestions
- [x] 10.3 Test /summary endpoint without corrections returns empty array
- [x] 10.4 Verify frontend displays IELTS suggestions in SummaryModal
