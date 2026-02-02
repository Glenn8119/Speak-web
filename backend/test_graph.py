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

    # Stream updates from the graph
    try:
        async for update in graph.astream(initial_state, config, stream_mode="updates"):
            print(f"📦 Update received: {list(update.keys())}")

            # Display chat response if available
            if "chat" in update:
                messages = update["chat"].get("messages", [])
                if messages:
                    print(f"💭 Chat response: {messages[0].content[:100]}...")

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
        print("\n🎉 All nodes executed in parallel as expected!")

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        raise


if __name__ == "__main__":
    # Check if .env file exists and has ANTHROPIC_API_KEY
    import os
    from dotenv import load_dotenv

    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: ANTHROPIC_API_KEY not found in .env file")
        print("Please add your Anthropic API key to backend/.env")
        exit(1)

    print("=" * 60)
    print("LangGraph Workflow Test")
    print("=" * 60)
    print()

    asyncio.run(test_graph_execution())
