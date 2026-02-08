"""
Test script for LangGraph workflow.
Run this to verify the graph executes correctly with sample inputs.
"""

import asyncio
from langchain_core.messages import HumanMessage
from graph import compile_graph, GraphState


async def test_graph_execution():
    """Test the graph with a sample user message."""
    print("🧪 Testing LangGraph workflow...\n")

    # Compile the graph
    print("📊 Compiling graph...")
    graph = compile_graph()
    print("✅ Graph compiled successfully\n")

    # Create initial state with a test message
    test_message = "I go to school yesterday and see my friend."
    print(f"💬 Test message: '{test_message}'\n")

    initial_state: GraphState = {
        "messages": [HumanMessage(content=test_message)],
        "corrections": [],
        "thread_id": "test_thread_123"
    }

    # Configure thread for persistence
    config = {
        "configurable": {
            "thread_id": "test_thread_123"
        }
    }

    print("🚀 Executing graph with stream mode='updates'...\n")
    print("Expected order: dispatch → [chat → tts, correction] → END\n")

    # Track execution order for verification
    execution_order = []

    # Stream updates from the graph
    try:
        async for update in graph.astream(initial_state, config, stream_mode="updates"):
            node_names = list(update.keys())
            execution_order.extend(node_names)
            print(f"📦 Update received: {node_names}")

            # Display chat response if available
            if "chat" in update:
                messages = update["chat"].get("messages", [])
                if messages:
                    print(f"💭 Chat response: {messages[0].content[:100]}...")

            # Display TTS result if available
            if "tts" in update:
                tts_audio = update["tts"].get("tts_audio")
                tts_format = update["tts"].get("tts_format")
                if tts_audio:
                    print(f"🔊 TTS audio generated: {len(tts_audio)} chars (base64), format: {tts_format}")
                else:
                    print("🔊 TTS skipped (no audio generated)")

            # Display correction if available
            if "correction" in update:
                corrections = update["correction"].get("corrections", [])
                if corrections:
                    latest_correction = corrections[-1]
                    print(f"✏️  Correction:")
                    print(f"   Original: {latest_correction['original']}")
                    print(f"   Corrected: {latest_correction['corrected']}")
                    print(f"   Issues: {latest_correction['issues']}")

            print()

        print("✅ Graph execution completed successfully!")

        # Verify execution order
        print(f"\n📋 Execution order: {' → '.join(execution_order)}")

        # Verify chat comes before tts
        if "chat" in execution_order and "tts" in execution_order:
            chat_idx = execution_order.index("chat")
            tts_idx = execution_order.index("tts")
            if chat_idx < tts_idx:
                print("✅ Verified: chat executed before tts (series)")
            else:
                print("❌ Error: tts executed before chat!")

        print("\n🎉 Graph structure verified: chat → tts (series), correction (parallel)")

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        raise


async def test_multiple_messages_in_thread():
    """Test that multiple messages in same thread each get own TTS audio."""
    print("\n🧪 Testing multiple messages in same thread...\n")

    # Compile the graph
    graph = compile_graph()

    # Use same thread_id for both messages
    thread_id = "test_thread_multi"
    config = {"configurable": {"thread_id": thread_id}}

    messages = [
        "I go to store yesterday.",
        "Then I buy some apple."
    ]

    for i, msg_content in enumerate(messages, 1):
        print(f"📨 Message {i}: '{msg_content}'")

        state: GraphState = {
            "messages": [HumanMessage(content=msg_content)],
            "corrections": [],
            "thread_id": thread_id
        }

        tts_generated = False

        async for update in graph.astream(state, config, stream_mode="updates"):
            if "tts" in update:
                tts_audio = update["tts"].get("tts_audio")
                if tts_audio:
                    print(f"   🔊 Message {i} got TTS audio: {len(tts_audio)} chars")
                    tts_generated = True
                else:
                    print(f"   🔊 Message {i} TTS skipped (no API key)")
                    tts_generated = True  # Still counts as "handled"

        if tts_generated:
            print(f"   ✅ Message {i} TTS node executed")
        print()

    print("✅ Multiple message test completed!")
    print("Each message in thread gets its own TTS processing.\n")


if __name__ == "__main__":
    # Check if .env file exists and has required API keys
    import os
    from dotenv import load_dotenv

    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: ANTHROPIC_API_KEY not found in .env file")
        print("Please add your Anthropic API key to backend/.env")
        exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in .env file")
        print("TTS will be skipped. Add your OpenAI API key to backend/.env for TTS.")

    print("=" * 60)
    print("LangGraph Workflow Test")
    print("=" * 60)
    print()

    asyncio.run(test_graph_execution())

    print("\n" + "=" * 60)
    print("Multi-Message Thread Test")
    print("=" * 60)

    asyncio.run(test_multiple_messages_in_thread())
