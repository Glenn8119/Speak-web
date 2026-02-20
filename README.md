# Speak Web - AI English Practice Chat

## Overview

![Overview](./assets/overview.png)

This project is a web-based clone inspired by the Speak app, bringing the same immersive voice-based learning experience to the web while leveraging modern AI technologies and architectural patterns.

This is a full-stack English practice application that enables users to have voice-based conversations with an AI partner. The system integrates Claude LLM for natural dialogue generation, OpenAI Whisper for speech-to-text transcription, and OpenAI TTS for realistic voice responses. A parallel grammar correction system provides real-time feedback on user messages, helping learners improve their English skills through practice.

## Key Highlights

**End-to-End Voice Conversation:** Users speak to practice English, with voice automatically transcribed via OpenAI Whisper API, and AI responses converted to natural-sounding speech via OpenAI TTS API, creating a fully voice-based immersive learning experience without typing.

**Real-time Grammar Correction:** A parallel analysis pipeline examines user messages for grammar errors and returns structured corrections without interrupting the conversation flow, processed simultaneously with the AI response.

**Guardrail for Content Filtering:** A guardrail system classifies user intent to ensure the conversation stays focused on English practice, rejecting off-topic or task-based requests.

**Conversation Summary & RAG Integration:** Post-conversation summaries include AI-generated learning tips and contextually relevant vocabulary suggestions using RAG (FAISS vector index with AWS Bedrock embeddings for semantic search).

## Technology Stack

- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4
- **Backend:** Python 3.13, FastAPI, LangGraph, LangChain
- **AI Integration:** Claude LLM (Anthropic SDK), OpenAI Whisper API, OpenAI TTS API
- **RAG Infrastructure:** FAISS vector index, AWS Bedrock Embeddings, LangChain

## Features

### Chat

![Chat-flow](./assets/chat-flow.png)

#### Parallel Execution for Low Latency

The LangGraph workflow is designed to minimize response latency through parallel execution. After the guardrail node classifies the user intent, the chat generation and grammar correction nodes run in parallel rather than sequentially. Additionally, results are emitted immediately as they become available via Server-Sent Events (SSE), allowing the frontend to start rendering and playing audio without waiting for the entire pipeline to complete.

### Summary

1. Generate personalized learning tips based on grammar corrections
2. Generate IELTS vocabulary suggestions to enhance sentences

#### RAG Implementation Approach

The IELTS vocabulary recommendation system uses a structured JSON format where each word is treated as an individual chunk in the FAISS vector index. To improve search accuracy, we employ a two-step process: before querying the vector store, we first use an LLM to extract relevant keywords from the conversation context. This keyword extraction step significantly enhances the precision of semantic search results.

## Development Notes

### Model Selection Strategy

To optimize costs while maintaining quality, we use different Claude models for different task complexities:

- **Haiku**: Used for conversational chat responses, keyword extraction, and intent classification (guardrail). Beyond cost savings, Haiku's faster inference significantly reduces Time To First Token (TTFT), improving overall system responsiveness for real-time interactions.
- **Sonnet**: Used for tasks requiring higher accuracy and structured output (grammar corrections, conversation summaries with pattern analysis)
