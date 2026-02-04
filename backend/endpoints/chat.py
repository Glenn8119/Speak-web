"""
Chat and summary endpoints with SSE streaming.
"""

import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from dependencies import get_graph
from schemas.chat import ChatRequest, SummaryRequest, SummaryResponse, PatternInfo

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

        # Summary tips prompt - focused on spoken English and encouraging tone
        system_prompt = """You are a warm, encouraging English speaking coach celebrating a student's practice session!

CONTEXT: This is a SPEAKING practice app. The corrections are from spoken English, not written text.
Focus your feedback on natural spoken English patterns, not written conventions.

Your task: Analyze the spoken grammar patterns and provide:
1. Identify common SPEAKING patterns that could be improved (with frequency)
2. Give 2-3 specific, actionable tips for speaking practice
3. Celebrate their effort and progress!

Important guidance:
- Focus on patterns that affect spoken clarity (tenses, agreement, articles, prepositions)
- Ignore capitalization/punctuation issues (these are from speech-to-text)
- Suggest practice activities they can do while speaking (e.g., "Try describing your day using past tense")
- Be genuinely warm and encouraging - speaking a new language takes courage!

Output format (JSON):
{
    "common_patterns": [
        {"pattern": "Name of speaking pattern", "frequency": N, "suggestion": "A specific speaking exercise to practice"}
    ],
    "tips": "A friendly 2-3 paragraph message that: (1) celebrates their effort and highlights something they did well, (2) explains 1-2 key patterns to focus on with simple tips, (3) ends with encouragement to keep speaking!"
}

Example tips format:
"Great job having this conversation! 🎉 You're getting more comfortable expressing your thoughts in English, and that's what matters most.

I noticed you sometimes mix up past and present tense when telling stories (like saying 'I go' instead of 'I went'). A fun way to practice: try narrating your daily activities out loud in past tense, even just for a few minutes!

Keep speaking - every conversation makes you more confident. You're doing amazing! 🌟"

Be enthusiastic and specific! Make them excited to keep practicing."""

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

            # Strip markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

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
