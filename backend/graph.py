"""
LangGraph workflow for Speak Chat App.
Defines the graph state and nodes for parallel chat and grammar correction.
"""

import logging
from typing import TypedDict, Annotated, Sequence

logger = logging.getLogger(__name__)
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class Correction(TypedDict):
    """Structure for grammar correction data."""
    original: str
    corrected: str
    issues: list[str]
    explanation: str
    message_id: str  # Reference to the user message being corrected


class GraphState(TypedDict):
    """
    State for the LangGraph workflow.

    Attributes:
        messages: Conversation history using LangChain message format.
                  Uses add_messages reducer to append new messages.
        corrections: List of grammar corrections for user messages.
        thread_id: Persistent conversation identifier for checkpointing.
        tts_audio: Base64-encoded audio from TTS (transient, not persisted).
        tts_format: Audio format (e.g., 'opus'). Transient, not persisted.
        guardrail_passed: Whether the user message passed the guardrail check.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    corrections: list[Correction]
    thread_id: str
    tts_audio: str | None
    tts_format: str | None
    guardrail_passed: bool | None


# Node implementations

def chat_node(state: GraphState) -> dict:
    """
    Generate conversational AI response to user messages.

    Uses a friendly, encouraging tone to promote continued English practice.
    Maintains context from conversation history.

    Args:
        state: Current graph state with conversation history

    Returns:
        Dictionary with updated messages containing AI response
    """
    logger.info(">>> chat_node started")
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import SystemMessage

    # Initialize the LLM
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",  # type: ignore
        temperature=0.7,  # Slightly creative for natural conversation
    )

    # Optimized system prompt for natural conversation (~40% fewer tokens)
    system_prompt = """You're a friendly conversation partner helping someone practice English.

Keep it casual and natural - chat like friends over coffee. Respond in 1-2 sentences, max 30 words. Show genuine interest with reactions like "Really?" or "That's cool!"

Key behaviors:
- Ask open follow-up questions (why/how, not yes/no)
- If they give short answers, invite elaboration: "Tell me more about that!"
- Never correct grammar - that's handled separately
- Celebrate their efforts: "Great point!" "I love that!"

Goal: Make speaking English feel fun, not like a test."""

    # Prepare messages with system prompt
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

    # Generate response
    response = llm.invoke(messages)

    logger.info("<<< chat_node finished")
    return {"messages": [response]}


def correction_node(state: GraphState) -> dict:
    """
    Analyze user's last message for grammar errors and provide corrections.

    Focuses on natural, conversational English rather than formal writing.
    Provides friendly, educational feedback.

    Args:
        state: Current graph state with conversation history

    Returns:
        Dictionary with updated corrections list
    """
    logger.info(">>> correction_node started")
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import SystemMessage, HumanMessage
    import json

    # Get the last user message
    user_messages = [msg for msg in state["messages"]
                     if hasattr(msg, 'type') and msg.type == "human"]
    if not user_messages:
        logger.info("<<< correction_node finished (no user messages)")
        return {"corrections": []}

    last_user_message = user_messages[-1]
    message_content = last_user_message.content

    # Generate a simple message ID (could use UUID in production)
    message_id = f"msg_{len(state['messages'])}"

    # Initialize the LLM
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",  # type: ignore
        temperature=0.3,  # Lower temperature for more consistent corrections
    )

    # Optimized system prompt for grammar correction (~50% fewer tokens)
    system_prompt = """Analyze spoken English for grammar errors. Input is from speech-to-text.

CORRECT these spoken grammar issues:
- Tenses: "I go yesterday" → "I went yesterday"
- Agreement: "She have" → "She has"
- Articles: "I bought car" → "I bought a car"
- Prepositions: "good in English" → "good at English"
- Word order: "what is it" → "what it is"
- Plurals: "two dog" → "two dogs"

IGNORE (not spoken errors):
- Capitalization, punctuation, spelling
- Informal speech: "gonna", "wanna", "um", "like"

Example:
Input: "yesterday i go to supermarket and buy many thing"
Correct output:
{
  "original": "yesterday i go to supermarket and buy many thing",
  "corrected": "yesterday I went to the supermarket and bought many things",
  "issues": ["Past tense: 'go' → 'went'", "Article: 'to supermarket' → 'to the supermarket'", "Past tense: 'buy' → 'bought'", "Plural: 'thing' → 'things'"],
  "explanation": "Great effort! Watch out for past tense when talking about yesterday, and remember 'the' before specific places like 'the supermarket'."
}


Input: "i think learning english is very fun"
Correct output:
{
  "original": "i think learning english is very fun",
  "corrected": "i think learning english is very fun",
  "issues": [],
  "explanation": "Perfect! Your grammar is spot on here. Great job! 🎉"
}

Output format (JSON):
{
  "original": "the exact transcribed message",
  "corrected": "grammar-corrected version (keep original capitalization/punctuation)",
  "issues": ["specific grammar error: 'wrong' → 'correct'"],
  "explanation": "A friendly 1-2 sentence explanation focused on the speaking error"
}

Be encouraging! Focus on helping them speak more naturally and confidently."""

    # Create the correction request
    correction_request = f"Please analyze this message for grammar errors:\n\n\"{message_content}\""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=correction_request)
    ]

    # Generate correction
    response = llm.invoke(messages)

    # Parse the JSON response
    try:
        from utils import strip_markdown_code_blocks

        # Ensure response.content is a string
        content = response.content if isinstance(
            response.content, str) else str(response.content)

        # Strip markdown code blocks if present (Claude sometimes wraps JSON)
        content = strip_markdown_code_blocks(content)

        correction_data = json.loads(content)
        correction = {
            "original": correction_data.get("original", message_content),
            "corrected": correction_data.get("corrected", message_content),
            "issues": correction_data.get("issues", []),
            "explanation": correction_data.get("explanation", ""),
            "message_id": message_id
        }

        # Append to corrections list
        new_corrections = state.get("corrections", []) + [correction]
        logger.info("<<< correction_node finished")
        return {"corrections": new_corrections}

    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        fallback_correction = {
            "original": message_content,
            "corrected": message_content,
            "issues": [],
            "explanation": "Unable to analyze grammar at this time.",
            "message_id": message_id
        }
        new_corrections = state.get("corrections", []) + [fallback_correction]
        logger.info("<<< correction_node finished (fallback)")
        return {"corrections": new_corrections}


def tts_node(state: GraphState) -> dict:
    """
    Generate text-to-speech audio for the AI chat response.

    Uses OpenAI TTS API with model 'tts-1', voice 'nova', format 'opus'.
    Audio is returned as base64-encoded data for SSE streaming.

    IMPORTANT: Audio data is NOT added to graph state to avoid bloating
    checkpoints. The audio is only returned in the stream output.

    Args:
        state: Current graph state with conversation history

    Returns:
        Dictionary with tts_audio (base64) and tts_format, or empty dict on error
    """
    logger.info(">>> tts_node started")
    import base64
    from openai import OpenAI

    # Get the last AI message from conversation history
    ai_messages = [msg for msg in state["messages"]
                   if hasattr(msg, 'type') and msg.type == "ai"]

    if not ai_messages:
        # No AI message to convert - skip TTS
        logger.info("<<< tts_node finished (no AI messages)")
        return {"tts_audio": None, "tts_format": None}

    last_ai_message = ai_messages[-1]
    text_content = last_ai_message.content

    # Handle empty or null chat responses (task 2.5)
    if not text_content or not text_content.strip():
        logger.info("<<< tts_node finished (empty response)")
        return {"tts_audio": None, "tts_format": None}

    try:
        # Initialize OpenAI client (reads OPENAI_API_KEY from env)
        client = OpenAI()

        # Call OpenAI TTS API (task 2.2)
        # Model: tts-1 (low latency), Voice: nova (friendly), Format: opus (small size)
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text_content,
            response_format="opus"
        )

        # Get audio bytes and encode as base64 (task 2.3)
        audio_bytes = response.content
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Return audio data for SSE streaming (task 2.6)
        # Note: This is NOT added to GraphState - only accessible during streaming
        logger.info("<<< tts_node finished")
        return {
            "tts_audio": audio_base64,
            "tts_format": "opus"
        }

    except Exception as e:
        # Error handling for TTS API failures (task 2.4)
        # Log error and continue without audio - don't block text response
        logger.error(
            "TTS generation failed",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "text_length": len(text_content) if text_content else 0,
            },
            exc_info=True
        )
        logger.info("<<< tts_node finished (error)")
        return {"tts_audio": None, "tts_format": None}


def chat_and_tts_node(state: GraphState) -> dict:
    """
    Combined chat + TTS node to avoid superstep blocking.

    LangGraph executes nodes in "supersteps" - all nodes in a superstep must
    complete before the next superstep begins. By combining chat and TTS into
    a single node, TTS can start immediately after chat completes without
    waiting for the parallel correction node.

    Args:
        state: Current graph state with conversation history

    Returns:
        Dictionary with both chat messages and TTS audio data
    """
    logger.info(">>> chat_and_tts_node started")

    # Step 1: Execute chat
    chat_result = chat_node(state)

    # Step 2: Execute TTS with updated state (includes new AI message)
    updated_state = {**state, **chat_result}
    tts_result = tts_node(updated_state)

    # Combine results
    combined_result = {**chat_result, **tts_result}

    logger.info("<<< chat_and_tts_node finished")
    return combined_result


def guardrail_node(state: GraphState) -> dict:
    """
    Classify user intent and filter task requests.

    Uses Claude Haiku to classify whether the user message is conversational
    (allowed) or a task request (rejected). Task requests receive a friendly
    rejection message that redirects to conversation practice.

    Args:
        state: Current graph state with conversation history

    Returns:
        Dictionary with guardrail_passed bool and optional rejection AIMessage
    """
    logger.info(">>> guardrail_node started")
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    import json

    # Get the last user message
    user_messages = [msg for msg in state["messages"]
                     if hasattr(msg, 'type') and msg.type == "human"]
    if not user_messages:
        logger.info("<<< guardrail_node finished (no user messages)")
        return {"guardrail_passed": True}

    last_user_message = user_messages[-1]
    message_content = last_user_message.content

    # Initialize Claude Haiku for fast classification
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",  # type: ignore
        temperature=0.3,  # Consistent classification
    )

    system_prompt = """You classify user messages for an English conversation practice app.

ALLOW (passed: true):
- Conversational messages about any topic
- Sharing experiences, opinions, feelings
- Asking for opinions or advice conversationally
- Discussing topics (tech, coding, travel, etc.) in conversation
- Greetings and small talk

REJECT (passed: false):
- Explicit task requests: "Write code for...", "Translate this...", "Solve this math..."
- Requests to generate, create, or produce content
- Homework or assignment help
- Translation requests

Key distinction: Talking ABOUT something (allowed) vs asking to DO something (rejected).

Examples:
- "I'm learning Python and it's really fun" → passed: true (sharing experience)
- "Write me a Python function to sort a list" → passed: false (task request)
- "What do you think about AI?" → passed: true (asking opinion)
- "Translate this paragraph to Chinese" → passed: false (task request)

Output JSON only:
{
  "passed": true/false,
  "response": null if passed, or friendly rejection message if not passed
}

For rejections, be warm and redirect to conversation (max 30 words):
- Acknowledge their interest
- Explain this is for conversation practice
- Suggest discussing the topic instead"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=f"Classify this message:\n\n\"{message_content}\"")
    ]

    response = llm.invoke(messages)

    # Parse JSON response
    try:
        from utils import strip_markdown_code_blocks

        content = response.content if isinstance(
            response.content, str) else str(response.content)
        content = strip_markdown_code_blocks(content)

        result = json.loads(content)
        passed = result.get("passed", True)

        if passed:
            logger.info("<<< guardrail_node finished (passed)")
            return {"guardrail_passed": True}
        else:
            # Return rejection message as AIMessage
            rejection_message = result.get("response",
                                           "I'm here to help you practice English conversation! "
                                           "Let's chat about topics you're interested in instead.")
            logger.info("<<< guardrail_node finished (rejected)")
            return {
                "guardrail_passed": False,
                "messages": [AIMessage(content=rejection_message)]
            }

    except json.JSONDecodeError:
        # On parse failure, allow the message through
        logger.info("<<< guardrail_node finished (parse error, passed)")
        return {"guardrail_passed": True}


# Graph construction

def route_after_guardrail(state: GraphState) -> list[str]:
    """
    Route after guardrail based on whether the message passed.

    If guardrail passed: fan out to chat_tts and correction nodes in parallel.
    If guardrail rejected: route to TTS to generate audio for rejection message.

    Args:
        state: Current graph state with guardrail_passed flag

    Returns:
        List of node names to route to
    """
    if state.get("guardrail_passed", True):
        return ["chat_tts", "correction"]
    else:
        return ["tts"]


def create_workflow():
    """
    Create the LangGraph workflow with guardrail, chat_tts and correction nodes.

    Graph structure:
        START -> guardrail -> [pass] -> chat_tts -> END
                           \         \-> correction -> END
                            -> [reject] -> tts -> END

    The guardrail node classifies intent first.
    On pass: chat_tts and correction run in parallel. chat_tts combines chat
             and TTS into a single node so TTS starts immediately after chat
             without waiting for correction to complete.
    On reject: TTS generates audio for the rejection message.

    Returns:
        Compiled StateGraph ready for execution
    """
    from langgraph.graph import StateGraph, END

    # Initialize the graph with our state schema
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("chat_tts", chat_and_tts_node)  # Combined chat + TTS
    workflow.add_node("tts", tts_node)  # Standalone TTS for guardrail rejections
    workflow.add_node("correction", correction_node)

    # Set entry point to guardrail
    workflow.set_entry_point("guardrail")

    # Add conditional edges from guardrail
    workflow.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        ["chat_tts", "correction", "tts"]
    )

    # chat_tts -> END (combined node, no longer needs separate tts edge)
    workflow.add_edge("chat_tts", END)

    # Standalone tts -> END (for guardrail rejections)
    workflow.add_edge("tts", END)

    # Correction -> END (parallel with chat_tts)
    workflow.add_edge("correction", END)

    return workflow


def get_checkpointer():
    """
    Get the appropriate checkpointer for thread persistence.

    Development: Uses MemorySaver (in-memory, simple setup)
    Production: TODO - Switch to Redis or PostgreSQL checkpointer

    Returns:
        Checkpointer instance for thread state persistence
    """
    from langgraph.checkpoint.memory import MemorySaver

    # For development, use in-memory checkpointer
    # TODO: For production, use Redis or PostgreSQL:
    # from langgraph.checkpoint.postgres import PostgresSaver
    # or
    # from langgraph.checkpoint.redis import RedisSaver

    return MemorySaver()


def compile_graph():
    """
    Compile the complete graph with checkpointer for execution.

    This creates the final executable graph instance with:
    - All nodes configured
    - Parallel execution edges
    - Thread persistence via checkpointer

    Returns:
        Compiled graph ready for streaming execution
    """
    workflow = create_workflow()
    checkpointer = get_checkpointer()

    # Compile with checkpointer for thread persistence
    graph = workflow.compile(checkpointer=checkpointer)

    return graph
