"""
Chat and summary endpoints with SSE streaming.
"""

import asyncio
import json
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from openai import OpenAI

from dependencies import get_graph, get_ielts_index
from ielts_rag import run_ielts_rag_pipeline
from schemas.chat import (
    CorrectionInfo,
    HistoryMessage,
    HistoryResponse,
    SummaryRequest,
    SummaryResponse,
    WordSuggestion,
)
from utils import strip_markdown_code_blocks

# Configure logger for chat endpoints
logger = logging.getLogger(__name__)


router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(
    audio: Annotated[UploadFile, File()],
    thread_id: Annotated[str | None, Form()] = None,
    graph: Annotated[CompiledStateGraph, Depends(get_graph)] = None
):
    """
    Stream AI conversation and grammar corrections via Server-Sent Events.

    Accepts audio file upload and optional thread_id for conversation persistence.
    Returns SSE stream with:
    - transcription event (transcribed text from audio)
    - thread_id event (for new conversations)
    - chat_response event (AI conversation response)
    - correction event (grammar correction data)
    - error event (if node fails)
    """
    # Generate thread_id for new conversations
    thread_id = thread_id or str(uuid.uuid4())

    # Read audio file bytes
    audio_bytes = await audio.read()

    # Initialize OpenAI client for Whisper API
    openai_client = OpenAI()

    # Variable to hold transcribed text
    transcribed_text = ""

    # Configuration for thread persistence
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    async def event_generator():
        """Generate SSE events from graph stream"""
        nonlocal transcribed_text
        try:
            # Step 1: Transcribe audio using Whisper API
            try:
                # Create a file-like object from audio bytes
                import io
                audio_file = io.BytesIO(audio_bytes)
                # Use the original filename (with extension) from the upload
                # This tells Whisper API the correct format (webm, mp4, wav, etc.)
                audio_file.name = audio.filename or "audio.webm"

                # Call Whisper API
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )

                transcribed_text = transcript.text

                # Emit transcription event immediately (before thread_id)
                import time
                transcription_data = {
                    "text": transcribed_text,
                    "timestamp": int(time.time())
                }
                yield f"event: transcription\ndata: {json.dumps(transcription_data)}\n\n"

            except Exception as whisper_error:
                # Log Whisper API error
                logger.error(
                    "Whisper API transcription failed",
                    extra={
                        "thread_id": thread_id,
                        "error_type": type(whisper_error).__name__,
                        "error_message": str(whisper_error),
                    },
                    exc_info=True
                )

                # Send error event for Whisper failure
                error_data = {
                    "node": "whisper",
                    "message": f"Speech recognition failed: {str(whisper_error)}",
                    "code": "STT_FAILED"
                }
                yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
                return  # Stop processing if transcription fails

            # Step 2: Send thread_id (for new conversations)
            yield f"event: thread_id\ndata: {json.dumps({'thread_id': thread_id})}\n\n"

            # Step 3: Create Graph input using transcribed text
            input_state = {
                "messages": [HumanMessage(content=transcribed_text)],
            }

            # Stream graph updates (use astream for true async streaming)
            chat_succeeded = False
            correction_succeeded = False

            async for update in graph.astream(input_state, config, stream_mode="updates"):
                # Each update is a dict with node name as key
                for node_name, node_output in update.items():
                    logger.info(f'Processing node: {node_name}')
                    try:
                        if node_name == "guardrail":
                            # Check if guardrail rejected the message
                            guardrail_passed = node_output.get(
                                "guardrail_passed", True)
                            if not guardrail_passed:
                                # Extract rejection message and emit as chat_response
                                messages = node_output.get("messages", [])
                                if messages:
                                    rejection_message = messages[0]
                                    chat_data = {
                                        "content": rejection_message.content,
                                        "role": "assistant",
                                        "rejected": True  # Flag to indicate this was a guardrail rejection
                                    }
                                    yield f"event: chat_response\ndata: {json.dumps(chat_data)}\n\n"
                                    chat_succeeded = True

                        elif node_name == "chat_tts":
                            # Combined chat + TTS node output
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

                            # Extract and stream audio data
                            tts_audio = node_output.get("tts_audio")
                            tts_format = node_output.get("tts_format")
                            if tts_audio:
                                audio_data = {
                                    "audio": tts_audio,
                                    "format": tts_format or "opus"
                                }
                                yield f"event: audio_chunk\ndata: {json.dumps(audio_data)}\n\n"

                        elif node_name == "correction":
                            # Extract the correction data
                            corrections = node_output.get("corrections", [])
                            if corrections:
                                # Get the last correction (the one just added)
                                correction = corrections[-1]
                                yield f"event: correction\ndata: {json.dumps(correction)}\n\n"
                                correction_succeeded = True

                        elif node_name == "tts":
                            # Extract and stream audio data (task 4.1, 4.2)
                            tts_audio = node_output.get("tts_audio")
                            tts_format = node_output.get("tts_format")
                            if tts_audio:
                                audio_data = {
                                    "audio": tts_audio,
                                    "format": tts_format or "opus"
                                }
                                yield f"event: audio_chunk\ndata: {json.dumps(audio_data)}\n\n"

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
                    "user_message": transcribed_text[:100] if transcribed_text else "(no transcription)",
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
    graph: Annotated[CompiledStateGraph, Depends(get_graph)],
    ielts_index: Annotated[FAISS | None, Depends(get_ielts_index)]
):
    """
    Generate a practice summary for a conversation thread.

    Parts:
    1. List all grammar corrections from thread state (no AI call)
    2. AI-generated tips based on correction analysis
    3. IELTS vocabulary suggestions based on corrected sentences (in parallel with tips)

    # to user's learning journal in Notion for long-term progress tracking.

    Args:
        request: SummaryRequest with thread_id

    Returns:
        SummaryResponse with corrections, tips, common patterns, and ielts_suggestions
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
                ielts_suggestions=[]
            )

        corrections = state.values.get("corrections", [])
        # Filter out corrections without issues
        corrections = [c for c in corrections if c.get("issues")]

        # Handle empty corrections (skip RAG pipeline)
        if not corrections:
            return SummaryResponse(
                corrections=[],
                tips="Excellent! You haven't made any grammar errors in this conversation. Keep up the great work! 🎉",
                ielts_suggestions=[]
            )

        # Part 2 & 3: Run tips generation and IELTS RAG pipeline in parallel
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

        # Task 6.2: Run tips and IELTS RAG in parallel
        async def generate_tips():
            """Generate tips using Claude Sonnet."""
            response = await llm.ainvoke(messages)
            return response

        async def generate_ielts_suggestions():
            """Run IELTS RAG pipeline (Task 6.4: graceful degradation)."""
            if ielts_index is None:
                logger.debug("IELTS index not available, skipping suggestions")
                return {"suggestions": []}

            try:
                # Extract corrected sentences from corrections
                corrected_sentences = [c.get("corrected", "")
                                       for c in corrections if c.get("corrected")]
                if not corrected_sentences:
                    return {"suggestions": []}

                return await run_ielts_rag_pipeline(corrected_sentences, ielts_index)
            except Exception as e:
                # Task 6.4: Graceful degradation - return empty on failure
                logger.warning(
                    f"IELTS RAG pipeline failed, returning empty suggestions: {e}")
                return {"suggestions": []}

        # Run both tasks in parallel
        tips_response, ielts_result = await asyncio.gather(
            generate_tips(),
            generate_ielts_suggestions()
        )

        # Parse tips AI response
        try:
            content = tips_response.content if isinstance(
                tips_response.content, str) else str(tips_response.content)

            # Strip markdown code blocks if present (Claude sometimes wraps JSON)
            content = strip_markdown_code_blocks(content)

            analysis = json.loads(content)

            tips = analysis.get(
                "tips", "Keep practicing! Every conversation helps you improve.")

        except (json.JSONDecodeError, KeyError):
            # Fallback if AI response can't be parsed
            tips = "Keep practicing! You're making great progress in your English conversation skills."

        # Convert IELTS suggestions to Pydantic models
        ielts_suggestions = [
            WordSuggestion(
                target_word=s.get("target_word", ""),
                ielts_word=s.get("ielts_word", ""),
                definition=s.get("definition", ""),
                example=s.get("example", ""),
                usage_context=s.get("usage_context", "")
            )
            for s in ielts_result.get("suggestions", [])
        ]

        return SummaryResponse(
            corrections=corrections,
            tips=tips,
            ielts_suggestions=ielts_suggestions
        )

    except Exception as e:
        # Return error response
        return SummaryResponse(
            corrections=[],
            tips=f"Unable to generate summary: {str(e)}",
            ielts_suggestions=[]
        )
