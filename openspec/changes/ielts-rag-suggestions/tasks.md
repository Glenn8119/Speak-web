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

- [ ] 3.1 Create backend/ielts_rag.py module
- [ ] 3.2 Implement keyword extraction function using Claude Haiku
- [ ] 3.3 Implement vector search function using FAISS
- [ ] 3.4 Implement suggestion generation function using Claude Sonnet
- [ ] 3.5 Create main pipeline function that orchestrates all steps

## 4. Schema Updates

- [ ] 4.1 Add WordSuggestion schema to backend/schemas/chat.py
- [ ] 4.2 Add IELTSSuggestion schema to backend/schemas/chat.py
- [ ] 4.3 Update SummaryResponse to include ielts_suggestions field

## 5. Dependency Injection

- [ ] 5.1 Add FAISS index loading function to backend/dependencies.py
- [ ] 5.2 Implement lifespan handler to load index at server startup
- [ ] 5.3 Create get_ielts_index dependency for endpoint injection

## 6. Endpoint Integration

- [ ] 6.1 Modify /summary endpoint to accept FAISS index dependency
- [ ] 6.2 Integrate IELTS RAG pipeline call in parallel with tips generation
- [ ] 6.3 Handle empty corrections case (skip RAG pipeline)
- [ ] 6.4 Implement graceful degradation on RAG failure

## 7. Testing

- [ ] 7.1 Verify server starts and loads FAISS index successfully
- [ ] 7.2 Test /summary endpoint with corrections returns ielts_suggestions
- [ ] 7.3 Test /summary endpoint without corrections returns empty array
