"""
Speak Chat App - Backend API
English practice application with AI-powered conversation and grammar correction.
"""

# Load environment variables first
from graph import compile_graph
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import json
import uuid
from dotenv import load_dotenv
load_dotenv()

# Import and compile graph once at module level
# This ensures the same MemorySaver instance is used across all requests
graph = compile_graph()


app = FastAPI(
    title="Speak Chat API",
    description="AI-powered English practice with real-time grammar corrections",
    version="0.1.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Speak Chat API is running"}


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "speak-chat-api",
        "version": "0.1.0"
    }


# Chat endpoint with SSE streaming


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    thread_id: str | None = None


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Stream AI conversation and grammar corrections via Server-Sent Events.

    Accepts a user message and optional thread_id for conversation persistence.
    Returns SSE stream with:
    - thread_id event (for new conversations)
    - chat_response event (AI conversation response)
    - correction event (grammar correction data)
    - error event (if node fails)
    """
    # Generate thread_id for new conversations
    thread_id = request.thread_id or str(uuid.uuid4())

    # Continuing conversation - only send new message
    input_state = {
        "messages": [HumanMessage(content=request.message)],
    }

    # Configuration for thread persistence
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    async def event_generator():
        """Generate SSE events from graph stream"""
        try:
            # Send thread_id first (for new conversations)
            if not request.thread_id:
                yield f"event: thread_id\ndata: {json.dumps({'thread_id': thread_id})}\n\n"

            # Stream graph updates
            for update in graph.stream(input_state, config, stream_mode="updates"):
                # Each update is a dict with node name as key
                for node_name, node_output in update.items():
                    if node_name == "chat":
                        # Extract the AI message
                        messages = node_output.get("messages", [])
                        if messages:
                            ai_message = messages[0]
                            chat_data = {
                                "content": ai_message.content,
                                "role": "assistant"
                            }
                            yield f"event: chat_response\ndata: {json.dumps(chat_data)}\n\n"

                    elif node_name == "correction":
                        # Extract the correction data
                        corrections = node_output.get("corrections", [])
                        if corrections:
                            # Get the last correction (the one just added)
                            correction = corrections[-1]
                            yield f"event: correction\ndata: {json.dumps(correction)}\n\n"

            # Send completion event
            yield f"event: complete\ndata: {json.dumps({'status': 'done'})}\n\n"

        except Exception as e:
            # Send error event
            error_data = {
                "error": str(e),
                "type": type(e).__name__
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering for nginx
        }
    )
