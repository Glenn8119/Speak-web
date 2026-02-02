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
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    corrections: list[Correction]
    thread_id: str


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

    # System prompt for natural, encouraging conversation
    system_prompt = """You are a friendly English conversation partner helping someone practice their English.

Your role:
- Have natural, everyday conversations using casual, spoken English
- Be encouraging and positive to build confidence
- Ask follow-up questions to keep the conversation flowing
- When users give short answers, ask open-ended questions to encourage elaboration
- Show genuine interest in what they share
- Use conversational phrases like "That's interesting!", "I see", "Tell me more about..."

Guidelines:
- Use natural, everyday English (not formal or academic)
- Keep responses concise but engaging (2-4 sentences typically)
- Avoid correcting grammar - that's handled separately
- Focus on maintaining an enjoyable conversation
- Be supportive and friendly, like talking to a friend

Remember: Your goal is to make English practice feel natural and fun!"""

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

    # System prompt for grammar correction
    system_prompt = """You are a friendly English grammar assistant helping someone improve their conversational English.

Your task: Analyze the user's message and provide grammar corrections in a structured format.

Focus on:
- Natural, everyday conversational English (not formal writing)
- Common grammar mistakes that affect clarity
- Verb tenses, subject-verb agreement, articles, prepositions
- Word order and sentence structure

Do NOT correct:
- Informal but acceptable conversational English (e.g., "wanna", "gonna")
- Casual contractions or colloquialisms
- Minor stylistic preferences

Output format (JSON):
{
  "original": "the exact user message",
  "corrected": "the corrected version (or same if perfect)",
  "issues": ["list of specific errors like 'Past tense: go → went'", "Article: 'the school' → 'school'"],
  "explanation": "A friendly 1-2 sentence explanation of the corrections"
}

If the message has no errors, return:
{
  "original": "the user message",
  "corrected": "the user message",
  "issues": [],
  "explanation": "Great! Your grammar is perfect here."
}

Be encouraging and supportive in your explanations!"""

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
        # Ensure response.content is a string
        content = response.content if isinstance(
            response.content, str) else str(response.content)

        # Strip markdown code blocks if present (Claude sometimes wraps JSON in ```json ... ```)
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        if content.startswith("```"):
            content = content[3:]  # Remove ```
        if content.endswith("```"):
            content = content[:-3]  # Remove trailing ```
        content = content.strip()

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
    Create the LangGraph workflow with parallel chat and correction nodes.

    Graph structure:
        START -> dispatch -> [chat_node, correction_node] -> END

    The chat and correction nodes execute in parallel, streaming results
    independently as they complete.

    Returns:
        Compiled StateGraph ready for execution
    """
    from langgraph.graph import StateGraph, END

    # Initialize the graph with our state schema
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("dispatch", dispatch_node)
    workflow.add_node("chat", chat_node)
    workflow.add_node("correction", correction_node)

    # Set entry point
    workflow.set_entry_point("dispatch")

    # Add parallel edges from dispatch to both chat and correction
    workflow.add_edge("dispatch", "chat")
    workflow.add_edge("dispatch", "correction")

    # Both nodes complete independently
    workflow.add_edge("chat", END)
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
