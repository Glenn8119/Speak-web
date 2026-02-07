"""
Chat and summary endpoints with SSE streaming.
"""

from schemas.chat import (
    ChatRequest,
    SummaryRequest,
    SummaryResponse,
    PatternInfo,
    HistoryResponse,
    HistoryMessage,
    CorrectionInfo,
)
from dependencies import get_graph
from utils import strip_markdown_code_blocks
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from fastapi.responses import StreamingResponse
import json
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

# Configure logger for chat endpoints
logger = logging.getLogger(__name__)


router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(
    request: ChatRequest,
    graph: Annotated[CompiledStateGraph, Depends(get_graph)]
):
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
            chat_succeeded = False
            correction_succeeded = False

            for update in graph.stream(input_state, config, stream_mode="updates"):
                # Each update is a dict with node name as key
                for node_name, node_output in update.items():
                    try:
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
                                chat_succeeded = True

                        elif node_name == "correction":
                            # Extract the correction data
                            corrections = node_output.get("corrections", [])
                            if corrections:
                                # Get the last correction (the one just added)
                                correction = corrections[-1]
                                yield f"event: correction\ndata: {json.dumps(correction)}\n\n"
                                correction_succeeded = True

                    except Exception as node_error:
                        # Log node-specific error
                        logger.error(
                            f"Error processing {node_name} node output",
                            extra={
                                "thread_id": thread_id,
                                "node_name": node_name,
                                "error_type": type(node_error).__name__,
                                "error_message": str(node_error),
                            },
                            exc_info=True
                        )

                        # Send node-specific error event
                        error_data = {
                            "node": node_name,
                            "message": f"Unable to get {node_name} response. The conversation can continue."
                        }
                        yield f"event: error\ndata: {json.dumps(error_data)}\n\n"

            # Send completion event with status
            completion_data = {
                "status": "done",
                "chat_succeeded": chat_succeeded,
                "correction_succeeded": correction_succeeded
            }
            yield f"event: complete\ndata: {json.dumps(completion_data)}\n\n"

        except Exception as e:
            # Log the error with full context
            logger.error(
                "Chat stream error",
                extra={
                    "thread_id": thread_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    # Truncate for logging
                    "user_message": request.message[:100],
                },
                exc_info=True
            )

            # Determine user-friendly error message
            error_type = type(e).__name__
            if "APIConnectionError" in error_type or "ConnectionError" in error_type:
                user_message = "Unable to connect to the AI service. Please try again in a moment."
            elif "RateLimitError" in error_type:
                user_message = "The service is busy right now. Please wait a moment and try again."
            elif "AuthenticationError" in error_type:
                user_message = "There's a configuration issue with the AI service. Please contact support."
            elif "Timeout" in error_type:
                user_message = "The request took too long. Please try again."
            else:
                user_message = "Something went wrong. Please try again."

            # Send error event with user-friendly message
            error_data = {
                "node": "unknown",
                "message": user_message,
                "error_type": error_type
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


@router.get("/history/{thread_id}", response_model=HistoryResponse)
async def get_history(
    thread_id: str,
    graph: Annotated[CompiledStateGraph, Depends(get_graph)]
):
    """
    Retrieve conversation history for a thread.

    Used to restore conversation state on page refresh.
    """
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    try:
        state = graph.get_state(config)

        if state is None or state.values is None:
            return HistoryResponse(messages=[])

        messages = state.values.get("messages", [])
        corrections = state.values.get("corrections", [])

        # Build a map of corrections by message index
        # Corrections have message_id like "msg_N" where N is the message index
        correction_map: dict[int, dict] = {}
        for correction in corrections:
            msg_id = correction.get("message_id", "")
            if msg_id.startswith("msg_"):
                try:
                    idx = int(msg_id.split("_")[1])
                    correction_map[idx] = correction
                except (ValueError, IndexError):
                    pass

        # Transform messages to frontend format
        result_messages: list[HistoryMessage] = []
        user_msg_count = 0

        for i, msg in enumerate(messages):
            msg_type = getattr(msg, "type", None)
            if msg_type == "human":
                role = "user"
                user_msg_count += 1
                # Find correction for this user message
                # Correction message_id uses 1-based index counting only user+assistant pairs
                correction_data = correction_map.get(i + 1)
                correction = None
                if correction_data:
                    correction = CorrectionInfo(
                        original=correction_data.get("original", ""),
                        corrected=correction_data.get("corrected", ""),
                        issues=correction_data.get("issues", []),
                        explanation=correction_data.get("explanation", "")
                    )
            elif msg_type == "ai":
                role = "assistant"
                correction = None
            else:
                continue

            result_messages.append(HistoryMessage(
                id=f"msg_{i}_{msg_type}",
                role=role,
                content=str(msg.content),
                timestamp=0,  # LangGraph doesn't store timestamps
                correction=correction
            ))

        return HistoryResponse(messages=result_messages)

    except Exception as e:
        # Return empty history on error
        return HistoryResponse(messages=[])


@router.post("/summary", response_model=SummaryResponse)
async def get_summary(
    request: SummaryRequest,
    graph: Annotated[CompiledStateGraph, Depends(get_graph)]
):
    """
    Generate a two-part practice summary for a conversation thread.

    Part 1: List all grammar corrections from thread state (no AI call)
    Part 2: AI-generated tips based on correction analysis

    # TODO: Future enhancement - Add Notion MCP sync to save summaries
    # to user's learning journal in Notion for long-term progress tracking.

    Args:
        request: SummaryRequest with thread_id

    Returns:
        SummaryResponse with corrections, tips, and common patterns
    """
    thread_id = request.thread_id

    # Part 1: Query thread state for corrections (no AI needed)
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    try:
        # Get state from the graph's checkpointer
        state = graph.get_state(config)

        if state is None or state.values is None:
            return SummaryResponse(
                corrections=[],
                tips="Start a conversation to get grammar feedback and personalized tips!",
                common_patterns=[]
            )

        corrections = state.values.get("corrections", [])

        # Handle empty corrections
        if not corrections:
            return SummaryResponse(
                corrections=[],
                tips="Excellent! You haven't made any grammar errors in this conversation. Keep up the great work! 🎉",
                common_patterns=[]
            )

        # Part 2: AI-powered tips generation
        llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",  # type: ignore
            temperature=0.5,
        )

        # Prepare corrections summary for AI
        corrections_text = "\n".join([
            f"- Original: \"{c['original']}\"\n  Corrected: \"{c['corrected']}\"\n  Issues: {c['issues']}"
            for c in corrections
        ])

        # Optimized summary tips prompt (~40% fewer tokens)
        system_prompt = """Analyze spoken English grammar patterns and give encouraging feedback.

From the corrections, identify:
1. Common patterns needing practice (with frequency count)
2. 2-3 actionable speaking tips

Focus on spoken clarity issues (tenses, agreement, articles). Ignore punctuation/capitalization.

Output format (JSON):
{
  "common_patterns": [{"pattern": "Pattern name", "frequency": N, "suggestion": "Practice exercise"}],
  "tips": "2-3 paragraphs: (1) Celebrate effort (2) Key pattern + simple tip (3) Encouragement"
}

Example tips: "Great conversation! 🎉 You're expressing yourself well.\n\nI noticed past/present tense mix-ups ('I go' vs 'I went'). Try narrating your day in past tense!\n\nKeep speaking - you're doing amazing! 🌟"

Be warm and specific!"""

        analysis_request = f"""Please analyze these grammar corrections from a conversation:

{corrections_text}

Total corrections: {len(corrections)}

Identify patterns and provide personalized tips."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=analysis_request)
        ]

        response = llm.invoke(messages)

        # Parse AI response
        try:
            content = response.content if isinstance(
                response.content, str) else str(response.content)

            # Strip markdown code blocks if present (Claude sometimes wraps JSON)
            content = strip_markdown_code_blocks(content)

            analysis = json.loads(content)

            tips = analysis.get(
                "tips", "Keep practicing! Every conversation helps you improve.")
            patterns_data = analysis.get("common_patterns", [])

            common_patterns = [
                PatternInfo(
                    pattern=p.get("pattern", "Unknown"),
                    frequency=p.get("frequency", 1),
                    suggestion=p.get("suggestion", "Practice makes perfect!")
                )
                for p in patterns_data
            ]

        except (json.JSONDecodeError, KeyError):
            # Fallback if AI response can't be parsed
            tips = "Keep practicing! You're making great progress in your English conversation skills."
            common_patterns = []

        return SummaryResponse(
            corrections=corrections,
            tips=tips,
            common_patterns=common_patterns
        )

    except Exception as e:
        # Return error response
        return SummaryResponse(
            corrections=[],
            tips=f"Unable to generate summary: {str(e)}",
            common_patterns=[]
        )
