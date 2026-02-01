# Speak-like Web Chat App - Architecture Summary

## 📋 Project Overview

A web-based English speaking practice application inspired by Speak. Users can practice conversational English with AI-powered grammar corrections and personalized learning tips.

**Core Philosophy**: Natural, everyday English practice - not formal writing correction.

---

## 🎯 Key Features

1. **AI Conversational Partner** - Natural, encouraging dialogue
2. **Real-time Grammar Corrections** - Message-level corrections with explanations
3. **Accordion UI** - Corrections hidden by default, expandable on click
4. **Practice Summary** - On-demand summary with AI-generated tips
5. **Persistent Conversations** - Survives page refresh via LangGraph threads
6. **New Conversation** - Button to start fresh session

---

## 🏗️ Technology Stack

### Backend

- **Framework**: FastAPI
- **AI Orchestration**: LangGraph (with Anthropic Claude)
- **LLM**: Anthropic Claude (via LangGraph ChatAnthropic)
- **Streaming**: Server-Sent Events (SSE)
- **Stream Mode**: `stream_mode="updates"` (complete node outputs, not token-by-token)
- **Persistence**: LangGraph checkpointer (thread-based state)

### Frontend

- **Framework**: React (likely with Vite)
- **Communication**: SSE client for real-time updates
- **State Management**: React Context/Zustand (TBD)
- **Storage**: localStorage for thread_id persistence

### Project Structure

```
speak-web/
├── frontend/          # React application
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── ...
│   └── package.json
└── backend/           # FastAPI + LangGraph
    ├── app/
    │   ├── graph/     # LangGraph workflow
    │   ├── api/       # FastAPI endpoints
    │   └── ...
    └── requirements.txt
```

---

## 🔄 Architecture Flow

```
┌─────────────────────────────────────────────────────────┐
│                    COMPLETE FLOW                        │
└─────────────────────────────────────────────────────────┘

1. User types message
   │
   ▼
2. Frontend → POST /chat
   • First message: no thread_id
   • Subsequent: includes thread_id
   │
   ▼
3. Backend (FastAPI)
   • Generates thread_id if needed
   • Invokes LangGraph with stream_mode="updates"
   │
   ▼
4. LangGraph Parallel Execution
   ┌─────────────┬─────────────┐
   │  Chat Node  │ Correction  │
   │  (Anthropic)│    Node     │
   │             │ (Anthropic) │
   └──────┬──────┴──────┬──────┘
          │             │
          │ (whichever finishes first)
          │             │
          ▼             ▼
5. SSE Stream Events
   • thread_id (first message only)
   • chat_response (complete AI response)
   • correction (complete correction object)
   • done (signal completion)
   │
   ▼
6. Frontend Updates UI
   • Stores thread_id in localStorage
   • Shows loading states for both
   • Updates as each event arrives
   • Attaches correction to user message
```

---

## 🎨 User Experience Flow

### Chat Interface

```
┌────────────────────────────────────────────────────────┐
│  User: "I go to school yesterday"                      │
│  ─────────────────────────────────────────────────     │
│  📝 Grammar correction available ▼                     │  ← Collapsed accordion
└────────────────────────────────────────────────────────┘
│
│  AI: "That's great! Tell me more about your day..."    │
└────────────────────────────────────────────────────────┘

                    ↓ (user clicks accordion)

┌────────────────────────────────────────────────────────┐
│  User: "I go to school yesterday"                      │
│  ─────────────────────────────────────────────────     │
│  📝 Grammar correction ▲                               │  ← Expanded
│  ┌──────────────────────────────────────────────────┐ │
│  │ ✅ Corrected:                                    │ │
│  │ "I went to school yesterday"                     │ │
│  │                                                  │ │
│  │ 📌 Issues found:                                │ │
│  │ • Past tense: "go" → "went"                     │ │
│  │                                                  │ │
│  │ 💡 Explanation:                                 │ │
│  │ Use past tense for actions completed yesterday  │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

### Loading States

Both chat and correction show loading indicators:

```
User: "I go to school yesterday"
📝 Checking grammar... ⏳
AI: Thinking... ⏳
```

---

## 🔌 API Endpoints

### 1. POST `/chat` (Streaming)

**Purpose**: Handle user messages, return AI response + grammar correction

**Request**:

```json
{
  "message": "I go to school yesterday",
  "thread_id": "thread_abc123" // Optional, null for first message
}
```

**Response**: SSE Stream

```
event: message
data: {"type": "thread_id", "thread_id": "thread_abc123"}

event: message
data: {"type": "correction", "correction": {...}}

event: message
data: {"type": "chat_response", "response": "That's great! ..."}

event: message
data: {"type": "done"}
```

**Correction Object Structure**:

```json
{
  "original": "I go to school yesterday",
  "corrected": "I went to school yesterday",
  "issues": ["Past tense: go → went"],
  "explanation": "Use past tense for actions completed in the past"
}
```

---

### 2. POST `/summary` (Request/Response)

**Purpose**: Generate practice summary from accumulated corrections

**Request**:

```json
{
  "thread_id": "thread_abc123"
}
```

**Response**:

```json
{
  "corrections": [
    {
      "original": "I go to school yesterday",
      "corrected": "I went to school yesterday",
      "issues": ["Past tense"]
    },
    {
      "original": "She don't like it",
      "corrected": "She doesn't like it",
      "issues": ["Subject-verb agreement"]
    }
  ],
  "tips": "You're making progress! Focus on past tense verbs...",
  "common_patterns": [
    {
      "pattern": "Past tense errors",
      "frequency": 3,
      "suggestion": "Review irregular verb conjugations"
    }
  ]
}
```

**Implementation Notes**:

- Part 1: List all corrections (query from thread state, no AI needed)
- Part 2: Generate tips (AI-powered analysis and suggestions)
- TODO: Future Notion MCP sync integration

---

## 🧩 LangGraph Workflow

### State Schema

```python
from typing import TypedDict, List, Annotated
from langgraph.graph import add_messages

class Message(TypedDict):
    role: str              # "user" | "assistant"
    content: str
    timestamp: str

class Correction(TypedDict):
    original: str
    corrected: str
    issues: List[str]
    explanation: str
    message_id: str

class GraphState(TypedDict):
    messages: Annotated[List[Message], add_messages]
    corrections: List[Correction]
    thread_id: str
```

### Graph Structure

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

workflow = StateGraph(GraphState)

# Nodes
workflow.add_node("dispatch", lambda state: state)  # Pass-through
workflow.add_node("chat_node", chat_node)
workflow.add_node("correction_node", correction_node)

# Edges (parallel execution)
workflow.set_entry_point("dispatch")
workflow.add_edge("dispatch", "chat_node")
workflow.add_edge("dispatch", "correction_node")
workflow.add_edge("chat_node", END)
workflow.add_edge("correction_node", END)

# Compile with checkpointer for persistence
checkpointer = MemorySaver()  # Use Redis/Postgres in production
graph_app = workflow.compile(checkpointer=checkpointer)
```

### Node Implementations

**Chat Node**:

```python
async def chat_node(state: GraphState):
    """Generate conversational response"""
    messages = state["messages"]

    system_prompt = """You are a friendly English conversation partner.
    Keep responses natural and encouraging. Ask follow-up questions.
    Focus on maintaining a natural conversation flow."""

    response = await llm.ainvoke([
        {"role": "system", "content": system_prompt},
        *messages
    ])

    return {"response": response.content}
```

**Correction Node**:

```python
async def correction_node(state: GraphState):
    """Generate grammar correction"""
    last_message = state["messages"][-1]["content"]

    system_prompt = """You are a grammar checker for everyday English.
    Analyze the message and provide:
    1. Corrected version (if needed)
    2. List of specific issues
    3. Brief, friendly explanation

    If grammar is perfect, return the original.
    Focus on natural, conversational English - not formal writing."""

    response = await llm.ainvoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Check this: {last_message}"}
    ])

    correction = parse_correction(response.content)
    return {"correction": correction}
```

---

## 🔐 Thread Management

### Thread Lifecycle

```
┌─────────────────────────────────────────────┐
│  First Message (no thread_id)              │
├─────────────────────────────────────────────┤
│  Backend: Generates new thread_id          │
│  Frontend: Stores in localStorage          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Subsequent Messages                        │
├─────────────────────────────────────────────┤
│  Frontend: Includes thread_id in request   │
│  Backend: Uses existing thread             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Page Refresh                               │
├─────────────────────────────────────────────┤
│  Frontend: Loads thread_id from localStorage│
│  Backend: Retrieves conversation history   │
│  User: Sees full conversation restored     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  "New Conversation" Button                  │
├─────────────────────────────────────────────┤
│  Frontend: Clears thread_id                │
│  Next message: Creates new thread          │
└─────────────────────────────────────────────┘
```

**Persistence**: Threads persist forever unless user clicks "New Conversation"

---

## 💾 Frontend State Management

### State Structure

```typescript
interface Message {
  role: 'user' | 'assistant'
  content: string
  correction?: Correction
  timestamp: string
}

interface Correction {
  original: string
  corrected: string
  issues: string[]
  explanation: string
}

interface ChatState {
  messages: Message[]
  threadId: string | null
  loading: {
    chat: boolean
    correction: boolean
  }
}
```

### SSE Event Handler

```typescript
const handleSSE = (event: MessageEvent) => {
  const data = JSON.parse(event.data)

  switch (data.type) {
    case 'thread_id':
      setThreadId(data.thread_id)
      localStorage.setItem('thread_id', data.thread_id)
      break

    case 'chat_response':
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString()
        }
      ])
      setLoading((prev) => ({ ...prev, chat: false }))
      break

    case 'correction':
      // Attach to last user message
      setMessages((prev) => {
        const updated = [...prev]
        const lastUserMsgIndex = updated.findLastIndex((m) => m.role === 'user')
        updated[lastUserMsgIndex].correction = data.correction
        return updated
      })
      setLoading((prev) => ({ ...prev, correction: false }))
      break

    case 'done':
      // All processing complete
      break
  }
}
```

---

## 🎯 Design Decisions

### Streaming Strategy

- **Mode**: `stream_mode="updates"` (complete node outputs)
- **Not token-by-token**: Simpler implementation, cleaner UX
- **Parallel execution**: Chat and correction run simultaneously
- **Order**: Either can finish first, frontend handles gracefully

### Correction Display

- **Level**: Message-level (one correction per user message)
- **UI**: Accordion component (collapsed by default)
- **Timing**: Shows after user sends message, not while typing
- **Focus**: Natural, everyday grammar - not formal English

### Summary Generation

- **Trigger**: User clicks "Summary" button anytime
- **Part 1**: List all corrections (no AI, query from state)
- **Part 2**: AI-generated tips and practice suggestions
- **Future**: Notion MCP sync (TODO comment for now)

---

## 🔮 Future Features

### Phase 2 (Planned)

1. **Voice Streaming** - Third LangGraph node for real-time TTS
2. **Notion Integration** - MCP-based sync for summaries
3. **Voice Input** - STT for spoken practice

### Voice Node Architecture (Future)

```
User message
      │
      ▼
┌──────────────┐
│   Dispatch   │
└──────┬───────┘
       │
       ├─────────────┬─────────────┬─────────────┐
       │             │             │             │
       ▼             ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│   Chat   │  │Correction│  │  Voice   │  │  Future  │
│   Node   │  │   Node   │  │  Node    │  │  Nodes   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
                                  │
                                  ▼
                            Streams audio
                            chunks for TTS
```

---

## 📝 Implementation Checklist

### Backend

- [ ] Set up FastAPI project structure
- [ ] Configure LangGraph with Anthropic
- [ ] Implement chat node with conversational prompt
- [ ] Implement correction node with grammar prompt
- [ ] Build parallel graph workflow
- [ ] Add checkpointer for thread persistence
- [ ] Create `/chat` SSE endpoint
- [ ] Create `/summary` endpoint
- [ ] Add error handling and logging
- [ ] Add TODO comment for Notion MCP sync

### Frontend

- [ ] Set up React + Vite project
- [ ] Create chat UI components
- [ ] Implement accordion component for corrections
- [ ] Build SSE client for streaming
- [ ] Add state management (Context/Zustand)
- [ ] Implement localStorage for thread_id
- [ ] Add "New Conversation" button
- [ ] Add "Summary" button and modal
- [ ] Handle loading states for both chat and correction
- [ ] Add error handling and retry logic

### Testing

- [ ] Test parallel node execution
- [ ] Test thread persistence across refresh
- [ ] Test "New Conversation" flow
- [ ] Test summary generation
- [ ] Test error scenarios (node failures, network issues)

---

## 🚀 Next Steps

Ready to start implementation! Options:

1. **`/opsx:new speak-chat-app`** - Step through proposal → design → tasks
2. **`/opsx:ff speak-chat-app`** - Fast-forward to implementation tasks

Choose based on preference for structured planning vs. rapid prototyping.

---

## 📚 Key References

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Stream Mode**: Use `stream_mode="updates"` for complete node outputs
- **Anthropic**: Claude via `ChatAnthropic` in LangGraph
- **SSE**: Server-Sent Events for real-time streaming
- **Checkpointer**: Thread-based persistence for conversation state

---

_Last Updated: 2026-01-31_
_Status: Architecture defined, ready for implementation_
