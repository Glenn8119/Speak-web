"""
Dependency injection utilities for FastAPI.
"""

from graph import compile_graph
from langgraph.graph.state import CompiledStateGraph

# Singleton graph instance
_graph: CompiledStateGraph | None = None


def get_graph() -> CompiledStateGraph:
    """
    Get the compiled LangGraph instance (singleton).

    This ensures the same MemorySaver instance is used across all requests,
    maintaining conversation persistence.
    """
    global _graph
    if _graph is None:
        _graph = compile_graph()
    return _graph
