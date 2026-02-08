"""
LangGraph workflow for Speak Chat App.
Defines the graph state and nodes for parallel chat and grammar correction.
"""

from typing import TypedDict, Annotated, Sequence
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
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    corrections: list[Correction]
    thread_id: str
    tts_audio: str | None
    tts_format: str | None


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
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import SystemMessage

    # Initialize the LLM
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",  # type: ignore
        temperature=0.7,  # Slightly creative for natural conversation
    )

    # Optimized system prompt for natural conversation (~40% fewer tokens)
    system_prompt = """You're a friendly conversation partner helping someone practice English.

Keep it casual and natural - chat like friends over coffee. Respond in 2-3 sentences. Show genuine interest with reactions like "Really?" or "That's cool!"

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
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import SystemMessage, HumanMessage
    import json

    # Get the last user message
    user_messages = [msg for msg in state["messages"]
                     if hasattr(msg, 'type') and msg.type == "human"]
    if not user_messages:
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
    import base64
    import logging
    from openai import OpenAI

    logger = logging.getLogger(__name__)

    # Get the last AI message from conversation history
    ai_messages = [msg for msg in state["messages"]
                   if hasattr(msg, 'type') and msg.type == "ai"]

    if not ai_messages:
        # No AI message to convert - skip TTS
        return {"tts_audio": None, "tts_format": None}

    last_ai_message = ai_messages[-1]
    text_content = last_ai_message.content

    # Handle empty or null chat responses (task 2.5)
    if not text_content or not text_content.strip():
        logger.info("TTS skipped: empty or null chat response")
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
        return {"tts_audio": None, "tts_format": None}


def dispatch_node(state: GraphState) -> dict:
    """
    Entry point for parallel execution of chat and correction nodes.

    This is a simple pass-through node that doesn't modify state.
    It serves as the starting point for the graph to fan out to
    both chat_node and correction_node in parallel.

    Args:
        state: Current graph state

    Returns:
        State with messages passed through
    """
    # Return messages unchanged - state passes through to parallel nodes
    return {"messages": state["messages"]}


# Graph construction

def create_workflow():
    """
    Create the LangGraph workflow with parallel chat/TTS and correction nodes.

    Graph structure:
        START -> dispatch -> chat -> tts -> END
                         \-> correction -----> END

    The chat node executes first, then TTS generates audio in series.
    The correction node runs in parallel with chat/tts chain.

    Returns:
        Compiled StateGraph ready for execution
    """
    from langgraph.graph import StateGraph, END

    # Initialize the graph with our state schema
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("dispatch", dispatch_node)
    workflow.add_node("chat", chat_node)
    workflow.add_node("tts", tts_node)
    workflow.add_node("correction", correction_node)

    # Set entry point
    workflow.set_entry_point("dispatch")

    # Add parallel edges from dispatch to chat and correction
    workflow.add_edge("dispatch", "chat")
    workflow.add_edge("dispatch", "correction")

    # Chat -> TTS -> END (series)
    workflow.add_edge("chat", "tts")
    workflow.add_edge("tts", END)

    # Correction -> END (parallel with chat/tts chain)
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
