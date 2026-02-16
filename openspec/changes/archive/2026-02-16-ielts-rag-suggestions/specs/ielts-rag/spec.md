## ADDED Requirements

### Requirement: IELTS suggestions in summary response
The `/summary` endpoint SHALL return an `ielts_suggestions` field containing vocabulary replacement suggestions from the official IELTS word list.

#### Scenario: Summary with corrections receives IELTS suggestions
- **WHEN** `/summary` is called with a conversation containing corrections
- **THEN** response includes `ielts_suggestions` array with vocabulary alternatives

#### Scenario: Summary without corrections skips IELTS suggestions
- **WHEN** `/summary` is called with a conversation containing no corrections
- **THEN** response includes empty `ielts_suggestions` array

### Requirement: Keyword extraction from corrected sentences
The system SHALL extract replaceable words and topic keywords from corrected sentences using Claude Haiku.

#### Scenario: Extract keywords from simple sentence
- **WHEN** processing corrected sentence "I went to the store yesterday"
- **THEN** system extracts replaceable words (e.g., "store", "went") and topic keywords (e.g., "shopping", "daily activities")

### Requirement: Vector search against IELTS vocabulary
The system SHALL search a pre-built FAISS index of IELTS words using Titan Embeddings to find relevant vocabulary alternatives.

#### Scenario: Find vocabulary alternatives for keyword
- **WHEN** searching for keyword "store"
- **THEN** system returns relevant IELTS words (e.g., "outlet", "retail", "shop") with definitions and examples

### Requirement: Generate vocabulary suggestions with context
The system SHALL generate vocabulary suggestions using Claude Sonnet that include the word, definition, example, and improved sentence.

#### Scenario: Generate suggestion with improved sentence
- **WHEN** processing target word "store" in sentence "I went to the store yesterday"
- **THEN** system generates suggestion with word, definition, example sentence, and improved version (e.g., "I went to the outlet yesterday")

### Requirement: FAISS index loaded at server startup
The system SHALL load the pre-built FAISS index into memory when the server starts.

#### Scenario: Server startup loads index
- **WHEN** server starts
- **THEN** FAISS index is loaded and ready for queries within 200ms

### Requirement: Graceful degradation on RAG failure
The system SHALL return empty `ielts_suggestions` if any part of the RAG pipeline fails, without affecting other summary fields.

#### Scenario: RAG pipeline timeout
- **WHEN** RAG pipeline exceeds timeout threshold
- **THEN** response includes empty `ielts_suggestions` array and other fields (tips, corrections, common_patterns) are unaffected
